#!/usr/bin/env python3
"""Pull ACS 5-year demographics for Butte County block groups.

For each block group inside the Chico area (per chico-geography-lookup.json),
fetches a curated set of variables (age, race/ethnicity, education, income,
tenure, citizen voting-age population) from the Census ACS API. Aggregates
the raw cohort variables into the buckets the candidate panel will display.

Output: public/data/_shared/butte-bg-acs.json — block-group-keyed dataset
shared across districts. Re-runs cache the raw API response to
.cache/census/butte-bg-acs-{year}.json so the API is hit at most once per
year of data per machine.

Usage:
    python3 scripts/pull-acs-block-groups.py
    python3 scripts/pull-acs-block-groups.py --year 2023
    python3 scripts/pull-acs-block-groups.py --refresh   # bypass cache
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_YEAR = 2023  # Most recent ACS 5-year as of writing
STATE_FIPS = "06"
COUNTY_FIPS = "007"

CACHE_DIR = PROJECT_ROOT / ".cache" / "census"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Variables to pull. The cohort indexes are well-documented in Census table shells.
# Grouped here so the post-processing aggregations stay readable.
AGE_MALE = [f"B01001_{i:03d}E" for i in range(3, 26)]     # 3..25 = male cohorts
AGE_FEMALE = [f"B01001_{i:03d}E" for i in range(27, 50)]  # 27..49 = female cohorts

RACE_VARS = {
    "B03002_001E": "race_total",
    "B03002_003E": "white_nh",
    "B03002_004E": "black_nh",
    "B03002_005E": "native_nh",
    "B03002_006E": "asian_nh",
    "B03002_007E": "pacific_nh",
    "B03002_008E": "other_nh",
    "B03002_009E": "two_or_more_nh",
    "B03002_012E": "hispanic",
}
EDUCATION_VARS = {
    "B15003_001E": "edu_total_25plus",
    "B15003_002E": "edu_no_school",
    "B15003_017E": "edu_hs",
    "B15003_018E": "edu_ged",
    "B15003_019E": "edu_some_college_lt1",
    "B15003_020E": "edu_some_college_1plus",
    "B15003_021E": "edu_associates",
    "B15003_022E": "edu_bachelors",
    "B15003_023E": "edu_masters",
    "B15003_024E": "edu_professional",
    "B15003_025E": "edu_doctorate",
}
INCOME_VARS = {
    "B19001_001E": "hh_total",
    "B19001_002E": "hh_lt_10k",
    "B19001_003E": "hh_10k_15k",
    "B19001_004E": "hh_15k_20k",
    "B19001_005E": "hh_20k_25k",
    "B19001_006E": "hh_25k_30k",
    "B19001_007E": "hh_30k_35k",
    "B19001_008E": "hh_35k_40k",
    "B19001_009E": "hh_40k_45k",
    "B19001_010E": "hh_45k_50k",
    "B19001_011E": "hh_50k_60k",
    "B19001_012E": "hh_60k_75k",
    "B19001_013E": "hh_75k_100k",
    "B19001_014E": "hh_100k_125k",
    "B19001_015E": "hh_125k_150k",
    "B19001_016E": "hh_150k_200k",
    "B19001_017E": "hh_200k_plus",
}
TENURE_VARS = {
    "B25003_001E": "tenure_total",
    "B25003_002E": "tenure_owner",
    "B25003_003E": "tenure_renter",
}
# Citizen Voting-Age Population — used as a proxy when no precinct-voter data is
# available. Sums native-born + naturalized over voting age.
# Denominator-side variables (008, 019) are direct "18 and over" subtotals;
# we use them to compute the CVAP rate, then apply that rate to BG adult pop.
CVAP_VARS = {
    "B05003_001E": "pop_total_for_cvap",
    "B05003_008E": "male_18plus_total",
    "B05003_009E": "male_native_18plus",
    "B05003_011E": "male_naturalized_18plus",
    "B05003_019E": "female_18plus_total",
    "B05003_020E": "female_native_18plus",
    "B05003_022E": "female_naturalized_18plus",
}
# Commute mode (B08006). Numbers from full table; we collapse to 6 buckets.
COMMUTE_VARS = {
    "B08006_001E": "commute_total_workers",
    "B08006_003E": "commute_drove_alone",
    "B08006_004E": "commute_carpooled",
    "B08006_008E": "commute_public_transit",
    "B08006_014E": "commute_bicycle",
    "B08006_015E": "commute_walked",
    "B08006_017E": "commute_work_from_home",
}
# Units in structure (B25024). Collapsed to single-family vs multi-family vs mobile.
STRUCTURE_VARS = {
    "B25024_001E": "structure_total_units",
    "B25024_002E": "structure_1_detached",
    "B25024_003E": "structure_1_attached",
    "B25024_004E": "structure_2",
    "B25024_005E": "structure_3_4",
    "B25024_006E": "structure_5_9",
    "B25024_007E": "structure_10_19",
    "B25024_008E": "structure_20_49",
    "B25024_009E": "structure_50_plus",
    "B25024_010E": "structure_mobile",
}
# Employment status (B23025). Working-age population breakdown.
EMPLOYMENT_VARS = {
    "B23025_001E": "lf_total_16plus",
    "B23025_002E": "lf_in_labor_force",
    "B23025_004E": "lf_employed",
    "B23025_005E": "lf_unemployed",
    "B23025_006E": "lf_armed_forces",
    "B23025_007E": "lf_not_in_labor_force",
}
# School enrollment (B14001).
SCHOOL_VARS = {
    "B14001_001E": "school_total_3plus",
    "B14001_004E": "school_kindergarten",
    "B14001_005E": "school_grade_1_4",
    "B14001_006E": "school_grade_5_8",
    "B14001_007E": "school_grade_9_12",
    "B14001_008E": "school_college_undergrad",
    "B14001_009E": "school_graduate_professional",
    "B14001_010E": "school_not_enrolled",
}
# SNAP / food stamps (B22001).
SNAP_VARS = {
    "B22001_001E": "snap_total_households",
    "B22001_002E": "snap_receiving",
    "B22001_003E": "snap_not_receiving",
}
# Gross rent as % of household income (B25070) — rent burden indicator.
RENT_BURDEN_VARS = {
    "B25070_001E": "rent_burden_total_with_cash_rent",
    "B25070_007E": "rent_burden_30_34pct",
    "B25070_008E": "rent_burden_35_39pct",
    "B25070_009E": "rent_burden_40_49pct",
    "B25070_010E": "rent_burden_50_plus",
}
# Geographic mobility (B07003). Recent movers.
MOBILITY_VARS = {
    "B07003_001E": "mobility_total",
    "B07003_004E": "mobility_same_house",
    "B07003_007E": "mobility_moved_within_county",
    "B07003_010E": "mobility_moved_within_state",
    "B07003_013E": "mobility_moved_from_other_state",
    "B07003_016E": "mobility_moved_from_abroad",
}
# Language spoken at home — collapsed (C16001). 5+ population.
LANGUAGE_VARS = {
    "C16001_001E": "lang_total_5plus",
    "C16001_002E": "lang_english_only",
    "C16001_003E": "lang_spanish",
    "C16001_006E": "lang_other_indo_european",
    "C16001_009E": "lang_asian_pacific_islander",
    "C16001_012E": "lang_other",
}
# Occupation (C24010, the collapsed/coarser version since B24010 was removed
# from the ACS 2023 5-year API). 5 broad categories per sex. Suppressed at BG
# level so pulled at tract level and proportioned to BGs.
OCCUPATION_VARS = {
    "C24010_001E": "occ_total_16plus",
    "C24010_003E": "occ_male_management_business_science_arts",
    "C24010_004E": "occ_male_service",
    "C24010_005E": "occ_male_sales_office",
    "C24010_006E": "occ_male_natural_resources_construction_maintenance",
    "C24010_007E": "occ_male_production_transportation_material_moving",
    "C24010_039E": "occ_female_management_business_science_arts",
    "C24010_040E": "occ_female_service",
    "C24010_041E": "occ_female_sales_office",
    "C24010_042E": "occ_female_natural_resources_construction_maintenance",
    "C24010_043E": "occ_female_production_transportation_material_moving",
}

ALL_VARS = (
    ["B01001_001E"]
    + AGE_MALE
    + AGE_FEMALE
    + list(RACE_VARS)
    + list(EDUCATION_VARS)
    + list(INCOME_VARS)
    + list(TENURE_VARS)
    + list(STRUCTURE_VARS)
    + list(EMPLOYMENT_VARS)
    + list(RENT_BURDEN_VARS)
    # The following are suppressed at BG level and must be pulled at tract level
    # then proportioned to BGs:
    #   - B08006 (commute), B14001 (school), B22001 (SNAP), C16001 (language),
    #     B07003 (mobility), B24010 (occupation), B05003 (CVAP).
)
TRACT_LEVEL_VARS = (
    list(CVAP_VARS)
    + list(OCCUPATION_VARS)
    + list(COMMUTE_VARS)
    + list(SCHOOL_VARS)
    + list(SNAP_VARS)
    + list(LANGUAGE_VARS)
    + list(MOBILITY_VARS)
)

# Map cohort indexes -> age bucket (matching the existing district-demographics
# profile script for consistency).
AGE_BUCKETS = {
    "under_18": list(range(3, 7)) + list(range(27, 31)),       # 0–17
    "age_18_34": list(range(7, 13)) + list(range(31, 37)),     # 18–34
    "age_35_54": list(range(13, 17)) + list(range(37, 41)),    # 35–54
    "age_55_64": list(range(17, 20)) + list(range(41, 44)),    # 55–64
    "age_65_plus": list(range(20, 26)) + list(range(44, 50)),  # 65+
}


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def chico_tracts() -> set[str]:
    """Tract IDs in the Chico place, from the existing lookup file."""
    lookup_path = Path(
        "/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
        "Smart Growth Advocates/research-code/census-api/chico-geography-lookup.json"
    )
    data = json.loads(lookup_path.read_text())
    return set(data["chico"]["census_tracts"])


def fetch_tract_cvap(year: int, api_key: str | None, refresh: bool) -> dict[str, dict]:
    """Pull all tract-level variables (CVAP + occupation + others suppressed at BG).
    Returns {tract_id: {var: value}}. Chunked to fit Census API's per-request limit.
    """
    cache_path = CACHE_DIR / f"butte-tract-extras-{year}.json"
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text())

    url = f"https://api.census.gov/data/{year}/acs/acs5"
    chunks = [TRACT_LEVEL_VARS[i : i + 45] for i in range(0, len(TRACT_LEVEL_VARS), 45)]
    by_tract: dict[str, dict] = {}
    print(f"  Pulling tract-level vars in {len(chunks)} chunk(s)...")
    for chunk_i, chunk in enumerate(chunks, start=1):
        params = {
            "get": ",".join(chunk),
            "for": "tract:*",
            "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
        }
        if api_key:
            params["key"] = api_key
        r = requests.get(url, params=params, timeout=60)
        if not r.ok:
            print(f"  tract chunk {chunk_i} FAILED: HTTP {r.status_code}", file=sys.stderr)
            continue
        rows = r.json()
        headers, data_rows = rows[0], rows[1:]
        for row in data_rows:
            rd = dict(zip(headers, row))
            tract = rd.get("tract")
            if not tract:
                continue
            if tract not in by_tract:
                by_tract[tract] = {}
            for v in chunk:
                by_tract[tract][v] = rd.get(v)
    cache_path.write_text(json.dumps(by_tract))
    print(f"  Cached tract-level data for {len(by_tract)} tracts")
    return by_tract


def fetch_acs(year: int, api_key: str | None, refresh: bool) -> list[list]:
    """Fetch ACS block-group rows for Butte County. Cached unless refresh."""
    cache_path = CACHE_DIR / f"butte-bg-acs-{year}.json"
    if cache_path.exists() and not refresh:
        print(f"Using cached ACS response: {cache_path}")
        return json.loads(cache_path.read_text())

    url = f"https://api.census.gov/data/{year}/acs/acs5"
    # Census caps `get` size — request in chunks of <=50 variables and merge.
    chunks = [ALL_VARS[i : i + 45] for i in range(0, len(ALL_VARS), 45)]
    print(f"Fetching ACS {year} 5-year for Butte County block groups "
          f"in {len(chunks)} chunk(s) of ≤45 variables each...")

    merged: dict[tuple, dict] = {}
    headers_seen: list[str] = []
    for chunk_i, chunk in enumerate(chunks, start=1):
        params = {
            "get": ",".join(chunk),
            "for": "block group:*",
            "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
        }
        if api_key:
            params["key"] = api_key
        t0 = time.time()
        r = requests.get(url, params=params, timeout=60)
        if not r.ok:
            print(f"  chunk {chunk_i} FAILED: HTTP {r.status_code} {r.text[:200]}",
                  file=sys.stderr)
            return []
        rows = r.json()
        headers, data_rows = rows[0], rows[1:]
        print(f"  chunk {chunk_i}: {len(data_rows)} rows in {time.time()-t0:.1f}s")
        var_cols = [h for h in headers if h.endswith("E")]
        geo_cols = ["state", "county", "tract", "block group"]
        for row in data_rows:
            row_dict = dict(zip(headers, row))
            key = tuple(row_dict[g] for g in geo_cols)
            if key not in merged:
                merged[key] = {g: row_dict[g] for g in geo_cols}
            for v in var_cols:
                merged[key][v] = row_dict[v]
        headers_seen = headers

    result = [["state", "county", "tract", "block group"] + ALL_VARS]
    for key in merged:
        row = merged[key]
        result.append(
            [row["state"], row["county"], row["tract"], row["block group"]]
            + [row.get(v, "0") for v in ALL_VARS]
        )

    cache_path.write_text(json.dumps(result))
    print(f"Cached {len(result)-1} block-group rows to {cache_path}")
    return result


def to_int(s) -> int:
    """ACS uses negative codes for missing values; treat those as 0."""
    try:
        v = int(s)
        return max(v, 0)
    except (ValueError, TypeError):
        return 0


def collapse_occupation(raw: dict) -> dict[str, int]:
    """Combine male+female occupation counts into 5 collapsed categories (C24010)."""
    pairs = [
        ("management_business_science_arts", "C24010_003E", "C24010_039E"),
        ("service", "C24010_004E", "C24010_040E"),
        ("sales_office", "C24010_005E", "C24010_041E"),
        ("natural_resources_construction_maintenance", "C24010_006E", "C24010_042E"),
        ("production_transportation_material_moving", "C24010_007E", "C24010_043E"),
    ]
    return {label: to_int(raw.get(m, 0)) + to_int(raw.get(f, 0)) for label, m, f in pairs}


def aggregate_row(raw: dict, geoid: str, tract_cvap_rate: float, adult_pop: int) -> dict:
    """Aggregate raw cohort vars into the buckets the UI panel will display.

    `tract_cvap_rate` is the parent tract's (CVAP / 18+ population) ratio; we use
    it to estimate this BG's CVAP since B05003 is suppressed at BG level.
    """
    age_buckets = {
        bucket: sum(to_int(raw.get(f"B01001_{i:03d}E", 0)) for i in idxs)
        for bucket, idxs in AGE_BUCKETS.items()
    }
    edu_total = to_int(raw.get("B15003_001E", 0))
    edu_hs = to_int(raw.get("B15003_017E", 0)) + to_int(raw.get("B15003_018E", 0))
    edu_some_college = sum(to_int(raw.get(f"B15003_{i:03d}E", 0)) for i in (19, 20, 21))
    edu_bachelors = to_int(raw.get("B15003_022E", 0))
    edu_grad = sum(to_int(raw.get(f"B15003_{i:03d}E", 0)) for i in (23, 24, 25))
    edu_less_hs = edu_total - (edu_hs + edu_some_college + edu_bachelors + edu_grad)
    edu_less_hs = max(edu_less_hs, 0)

    income_total = to_int(raw.get("B19001_001E", 0))
    income_low = sum(to_int(raw.get(f"B19001_{i:03d}E", 0)) for i in range(2, 6))     # <25k
    income_lower_mid = sum(to_int(raw.get(f"B19001_{i:03d}E", 0)) for i in range(6, 11))  # 25–50k
    income_mid = sum(to_int(raw.get(f"B19001_{i:03d}E", 0)) for i in (11, 12))         # 50–75k
    income_upper_mid = sum(to_int(raw.get(f"B19001_{i:03d}E", 0)) for i in (13, 14))   # 75–125k
    income_high = sum(to_int(raw.get(f"B19001_{i:03d}E", 0)) for i in (15, 16, 17))    # 125k+

    # B05003 is suppressed at BG level; estimate from tract rate × this BG's adult pop.
    cvap_estimated = round(adult_pop * tract_cvap_rate)

    return {
        "geoid": geoid,
        "tract": geoid[5:11],
        "block_group": geoid[11:],
        "total_population": to_int(raw.get("B01001_001E", 0)),
        "adult_population_18plus": adult_pop,
        "citizen_voting_age_population": cvap_estimated,
        "cvap_method": "estimated_from_tract_rate",
        "age": age_buckets,
        "race_ethnicity": {
            "white_nh": to_int(raw.get("B03002_003E", 0)),
            "black_nh": to_int(raw.get("B03002_004E", 0)),
            "native_nh": to_int(raw.get("B03002_005E", 0)),
            "asian_nh": to_int(raw.get("B03002_006E", 0)),
            "pacific_nh": to_int(raw.get("B03002_007E", 0)),
            "other_nh": to_int(raw.get("B03002_008E", 0)),
            "two_or_more_nh": to_int(raw.get("B03002_009E", 0)),
            "hispanic": to_int(raw.get("B03002_012E", 0)),
        },
        "education_25plus": {
            "less_than_hs": edu_less_hs,
            "high_school": edu_hs,
            "some_college": edu_some_college,
            "bachelors": edu_bachelors,
            "graduate": edu_grad,
        },
        "household_income": {
            "low_under_25k": income_low,
            "lower_mid_25_50k": income_lower_mid,
            "mid_50_75k": income_mid,
            "upper_mid_75_125k": income_upper_mid,
            "high_125k_plus": income_high,
            "total_households": income_total,
        },
        "tenure": {
            "owner": to_int(raw.get("B25003_002E", 0)),
            "renter": to_int(raw.get("B25003_003E", 0)),
            "total": to_int(raw.get("B25003_001E", 0)),
        },
        "commute": {
            "total_workers": to_int(raw.get("B08006_001E", 0)),
            "drove_alone": to_int(raw.get("B08006_003E", 0)),
            "carpooled": to_int(raw.get("B08006_004E", 0)),
            "public_transit": to_int(raw.get("B08006_008E", 0)),
            "bicycle": to_int(raw.get("B08006_014E", 0)),
            "walked": to_int(raw.get("B08006_015E", 0)),
            "work_from_home": to_int(raw.get("B08006_017E", 0)),
        },
        "housing_structure": {
            "total_units": to_int(raw.get("B25024_001E", 0)),
            "single_family": (
                to_int(raw.get("B25024_002E", 0))
                + to_int(raw.get("B25024_003E", 0))
            ),
            "small_multifamily_2_9": sum(to_int(raw.get(f"B25024_{i:03d}E", 0)) for i in (4, 5, 6)),
            "large_multifamily_10plus": sum(to_int(raw.get(f"B25024_{i:03d}E", 0)) for i in (7, 8, 9)),
            "mobile_home": to_int(raw.get("B25024_010E", 0)),
        },
        "employment": {
            "total_16plus": to_int(raw.get("B23025_001E", 0)),
            "employed": to_int(raw.get("B23025_004E", 0)),
            "unemployed": to_int(raw.get("B23025_005E", 0)),
            "not_in_labor_force": to_int(raw.get("B23025_007E", 0)),
        },
        "school_enrollment": {
            "total_3plus": to_int(raw.get("B14001_001E", 0)),
            "k12": sum(to_int(raw.get(f"B14001_{i:03d}E", 0)) for i in (4, 5, 6, 7)),
            "college_undergrad": to_int(raw.get("B14001_008E", 0)),
            "graduate_professional": to_int(raw.get("B14001_009E", 0)),
            "not_enrolled": to_int(raw.get("B14001_010E", 0)),
        },
        "snap_assistance": {
            "total_households": to_int(raw.get("B22001_001E", 0)),
            "receiving": to_int(raw.get("B22001_002E", 0)),
        },
        "rent_burden": {
            "renters_with_cash_rent": to_int(raw.get("B25070_001E", 0)),
            "burdened_30_plus_pct": sum(to_int(raw.get(f"B25070_{i:03d}E", 0)) for i in (7, 8, 9, 10)),
            "severely_burdened_50_plus_pct": to_int(raw.get("B25070_010E", 0)),
        },
        "mobility": {
            "total": to_int(raw.get("B07003_001E", 0)),
            "same_house_year_ago": to_int(raw.get("B07003_004E", 0)),
            "moved_within_county": to_int(raw.get("B07003_007E", 0)),
            "moved_within_state": to_int(raw.get("B07003_010E", 0)),
            "moved_from_other_state": to_int(raw.get("B07003_013E", 0)),
            "moved_from_abroad": to_int(raw.get("B07003_016E", 0)),
        },
        "language_at_home": {
            "total_5plus": to_int(raw.get("C16001_001E", 0)),
            "english_only": to_int(raw.get("C16001_002E", 0)),
            "spanish": to_int(raw.get("C16001_003E", 0)),
            "other_indo_european": to_int(raw.get("C16001_006E", 0)),
            "asian_pacific_islander": to_int(raw.get("C16001_009E", 0)),
            "other": to_int(raw.get("C16001_012E", 0)),
        },
        "occupation": collapse_occupation(raw),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--refresh", action="store_true",
                        help="Bypass the API response cache.")
    args = parser.parse_args()

    env = load_env(PROJECT_ROOT / ".env")
    api_key = env.get("CENSUS_API_KEY") or os.environ.get("CENSUS_API_KEY")
    if api_key:
        print(f"Using Census API key from .env ({api_key[:6]}…)")
    else:
        print("No CENSUS_API_KEY found — running anonymous (500 req/day limit). "
              "Sign up at https://api.census.gov/data/key_signup.html for unlimited.")

    print("Fetching tract-level CVAP + occupation (suppressed at BG level)...")
    tract_extras = fetch_tract_cvap(args.year, api_key, args.refresh)
    # Per-tract CVAP rate = (Native 18+ + Naturalized 18+) / Total 18+
    tract_cvap_rate: dict[str, float] = {}
    # Per-tract occupation share: { tract_id: { var_code: share } } where share is
    # the fraction of the tract's employed 16+ pop in that occupation category.
    tract_occ_shares: dict[str, dict[str, float]] = {}
    for tract_id, vars_ in tract_extras.items():
        total_18plus = (
            to_int(vars_.get("B05003_008E"))   # Male 18+ total
            + to_int(vars_.get("B05003_019E"))  # Female 18+ total
        )
        cvap = (
            to_int(vars_.get("B05003_009E"))   # Male 18+ Native
            + to_int(vars_.get("B05003_011E"))  # Male 18+ Naturalized
            + to_int(vars_.get("B05003_020E"))  # Female 18+ Native
            + to_int(vars_.get("B05003_022E"))  # Female 18+ Naturalized
        )
        tract_cvap_rate[tract_id] = (cvap / total_18plus) if total_18plus else 0.0

        tract_emp = to_int(vars_.get("C24010_001E"))
        if tract_emp > 0:
            tract_occ_shares[tract_id] = {
                v: to_int(vars_.get(v, 0)) / tract_emp
                for v in OCCUPATION_VARS
                if v != "C24010_001E"
            }
        else:
            tract_occ_shares[tract_id] = {}

    # For tract-level vars proportioned by their natural denominator:
    # commute → workers, school → pop 3+, SNAP → households, language → pop 5+,
    # mobility → total pop. We compute "rate" (per-pop share) at tract level here,
    # then apply to BG's matching denominator below.
    def proportion_rates(vars_dict: dict[str, str], denom_var: str) -> dict[str, dict[str, float]]:
        rates: dict[str, dict[str, float]] = {}
        for t, td in tract_extras.items():
            denom = to_int(td.get(denom_var, 0))
            if denom == 0:
                rates[t] = {}
                continue
            rates[t] = {v: to_int(td.get(v, 0)) / denom for v in vars_dict if v != denom_var}
        return rates

    tract_commute_rates = proportion_rates(COMMUTE_VARS, "B08006_001E")
    tract_school_rates = proportion_rates(SCHOOL_VARS, "B14001_001E")
    tract_snap_rates = proportion_rates(SNAP_VARS, "B22001_001E")
    tract_language_rates = proportion_rates(LANGUAGE_VARS, "C16001_001E")
    tract_mobility_rates = proportion_rates(MOBILITY_VARS, "B07003_001E")

    rows = fetch_acs(args.year, api_key, args.refresh)
    if not rows:
        return 1

    headers, data_rows = rows[0], rows[1:]
    print(f"Total Butte County block groups fetched: {len(data_rows)}")

    chico_tract_set = chico_tracts()
    print(f"Filtering to Chico ({len(chico_tract_set)} tracts)...")

    processed = {}
    for row in data_rows:
        raw = dict(zip(headers, row))
        tract = raw["tract"]
        if tract not in chico_tract_set:
            continue
        bg = raw["block group"]
        geoid = f"{raw['state']}{raw['county']}{tract}{bg}"
        # Compute adult population for this BG from cohorts
        adult_pop = sum(
            to_int(raw.get(f"B01001_{i:03d}E", 0))
            for i in AGE_BUCKETS["age_18_34"]
                  + AGE_BUCKETS["age_35_54"]
                  + AGE_BUCKETS["age_55_64"]
                  + AGE_BUCKETS["age_65_plus"]
        )
        rate = tract_cvap_rate.get(tract, 0.0)

        # Estimate BG-level counts for vars suppressed at BG level. For each, the
        # tract rate (per natural denominator) × BG's denominator → BG estimate.
        bg_pop = to_int(raw.get("B01001_001E", 0))
        bg_employed = to_int(raw.get("B23025_004E", 0))
        bg_hh = to_int(raw.get("B19001_001E", 0))

        # Occupation — proportion by employed
        shares = tract_occ_shares.get(tract, {})
        for v in OCCUPATION_VARS:
            if v == "C24010_001E":
                raw[v] = bg_employed
            else:
                raw[v] = round(bg_employed * shares.get(v, 0.0))

        # Commute — proportion by BG employed (workers ≈ employed)
        for v, r in tract_commute_rates.get(tract, {}).items():
            raw[v] = round(bg_employed * r)
        raw["B08006_001E"] = bg_employed

        # School enrollment — proportion by BG total population
        for v, r in tract_school_rates.get(tract, {}).items():
            raw[v] = round(bg_pop * r)
        raw["B14001_001E"] = bg_pop

        # SNAP — proportion by BG households
        for v, r in tract_snap_rates.get(tract, {}).items():
            raw[v] = round(bg_hh * r)
        raw["B22001_001E"] = bg_hh

        # Language — proportion by BG total population (approximation of 5+ pop)
        for v, r in tract_language_rates.get(tract, {}).items():
            raw[v] = round(bg_pop * r)
        raw["C16001_001E"] = bg_pop

        # Mobility — proportion by BG total population
        for v, r in tract_mobility_rates.get(tract, {}).items():
            raw[v] = round(bg_pop * r)
        raw["B07003_001E"] = bg_pop

        processed[geoid] = aggregate_row(raw, geoid, rate, adult_pop)

    print(f"Kept {len(processed)} Chico block groups")

    output = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": f"ACS 5-year {args.year}",
        "state_fips": STATE_FIPS,
        "county_fips": COUNTY_FIPS,
        "block_group_count": len(processed),
        "block_groups": processed,
    }

    out_dir = PROJECT_ROOT / "public" / "data" / "_shared"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "butte-bg-acs.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
