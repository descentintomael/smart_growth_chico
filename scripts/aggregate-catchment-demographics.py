#!/usr/bin/env python3
"""Aggregate ACS block-group demographics into per-venue catchment summaries.

For each venue × profile (walk_10, walk_15, bike_10, bike_15) we:
  1. Find block groups that intersect the catchment polygon.
  2. Compute an areal weight per intersecting BG = (intersection area) / (BG total area).
  3. Apply the weight to each BG's count variables and sum.

The output captures everything needed by the per-venue demographics panel:
  - estimated residents, estimated CVAP (citizen voting-age proxy for registered voters)
  - age, race/ethnicity, education, income, tenure distributions
  - bg_count and total catchment area for QA

Block-group polygons come from the Census TIGERweb REST API filtered to
Butte County; cached locally so re-runs are offline.

Output: public/data/candidate-district-{N}/catchment-demographics.json

Usage:
    python3 scripts/aggregate-catchment-demographics.py 6
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import shape as shape_from_geom

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / ".cache" / "tiger"

# Census TIGERweb REST endpoint for Block Groups (current vintage).
TIGERWEB_BG_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
    "tigerWMS_Current/MapServer/10/query"
)
STATE_FIPS = "06"
COUNTY_FIPS = "007"


def district_dir(n: int) -> Path:
    return PROJECT_ROOT / "public" / "data" / f"candidate-district-{n}"


def load_or_fetch_bg_polygons() -> gpd.GeoDataFrame:
    """Pull Butte County BG polygons from TIGERweb. Cached."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"butte-bg-polygons.geojson"
    if cache_path.exists():
        print(f"Loading cached BG polygons from {cache_path}")
        return gpd.read_file(cache_path)

    print("Fetching Butte County block-group polygons from TIGERweb...")
    params = {
        "where": f"STATE='{STATE_FIPS}' AND COUNTY='{COUNTY_FIPS}'",
        "outFields": "GEOID,STATE,COUNTY,TRACT,BLKGRP",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    r = requests.get(TIGERWEB_BG_URL, params=params, timeout=120)
    r.raise_for_status()
    cache_path.write_text(r.text)
    gdf = gpd.read_file(cache_path)
    print(f"  Got {len(gdf)} block-group polygons")
    return gdf


def load_demographics() -> dict:
    """Load the ACS-derived demographics keyed by GEOID."""
    path = PROJECT_ROOT / "public" / "data" / "_shared" / "butte-bg-acs.json"
    if not path.exists():
        print(
            f"butte-bg-acs.json not found: {path}\n"
            f"Run scripts/pull-acs-block-groups.py first.",
            file=sys.stderr,
        )
        sys.exit(1)
    return json.loads(path.read_text())["block_groups"]


def load_or_fetch_fec_zctas():
    """Load Chico ZCTA polygons + the FEC by-ZIP donor totals. Returns
    (gdf, fec_data) or (None, None) if either is missing."""
    zcta_path = PROJECT_ROOT / "public" / "data" / "_shared" / "butte-zctas.geojson"
    fec_path = PROJECT_ROOT / "public" / "data" / "_shared" / "fec-chico-by-zip.json"
    if not zcta_path.exists() or not fec_path.exists():
        return None, None
    gdf = gpd.read_file(zcta_path).to_crs(epsg=2226)
    gdf["geometry"] = gdf.geometry.buffer(0)
    gdf["zcta_area_ft2"] = gdf.geometry.area
    gdf["zip5"] = gdf["BASENAME"].astype(str)
    fec_data = json.loads(fec_path.read_text())["by_zip"]
    return gdf, fec_data


def load_or_fetch_precincts(election: str):
    """Load SWDB precincts for a given election (g24, g22, ...). Returns None
    if the file isn't present so the aggregator can skip cleanly."""
    path = PROJECT_ROOT / "public" / "data" / "_shared" / f"butte-precincts-{election}.geojson"
    # Backwards compatibility: also try the unsuffixed name.
    if not path.exists():
        legacy = PROJECT_ROOT / "public" / "data" / "_shared" / "butte-precincts.geojson"
        if not legacy.exists():
            return None
        path = legacy
    g = gpd.read_file(path).to_crs(epsg=2226)
    g["geometry"] = g.geometry.buffer(0)  # fix topology issues
    g["precinct_area_ft2"] = g.geometry.area
    return g


# Flat path → value extractor for the deep demographic dict.
# Each entry: (output_key, (path tuple from BG record root))
# Plus a derived "total_population" / "citizen_voting_age_population" at top level.
COUNT_PATHS = [
    ("total_population", ("total_population",)),
    ("adult_population_18plus", ("adult_population_18plus",)),
    ("citizen_voting_age_population", ("citizen_voting_age_population",)),
    ("age_under_18", ("age", "under_18")),
    ("age_18_34", ("age", "age_18_34")),
    ("age_35_54", ("age", "age_35_54")),
    ("age_55_64", ("age", "age_55_64")),
    ("age_65_plus", ("age", "age_65_plus")),
    ("race_white_nh", ("race_ethnicity", "white_nh")),
    ("race_black_nh", ("race_ethnicity", "black_nh")),
    ("race_native_nh", ("race_ethnicity", "native_nh")),
    ("race_asian_nh", ("race_ethnicity", "asian_nh")),
    ("race_pacific_nh", ("race_ethnicity", "pacific_nh")),
    ("race_other_nh", ("race_ethnicity", "other_nh")),
    ("race_two_or_more_nh", ("race_ethnicity", "two_or_more_nh")),
    ("race_hispanic", ("race_ethnicity", "hispanic")),
    ("edu_less_than_hs", ("education_25plus", "less_than_hs")),
    ("edu_high_school", ("education_25plus", "high_school")),
    ("edu_some_college", ("education_25plus", "some_college")),
    ("edu_bachelors", ("education_25plus", "bachelors")),
    ("edu_graduate", ("education_25plus", "graduate")),
    ("income_low_under_25k", ("household_income", "low_under_25k")),
    ("income_lower_mid_25_50k", ("household_income", "lower_mid_25_50k")),
    ("income_mid_50_75k", ("household_income", "mid_50_75k")),
    ("income_upper_mid_75_125k", ("household_income", "upper_mid_75_125k")),
    ("income_high_125k_plus", ("household_income", "high_125k_plus")),
    ("households_total", ("household_income", "total_households")),
    ("tenure_owner", ("tenure", "owner")),
    ("tenure_renter", ("tenure", "renter")),
    # Commute mode
    ("commute_total_workers", ("commute", "total_workers")),
    ("commute_drove_alone", ("commute", "drove_alone")),
    ("commute_carpooled", ("commute", "carpooled")),
    ("commute_public_transit", ("commute", "public_transit")),
    ("commute_bicycle", ("commute", "bicycle")),
    ("commute_walked", ("commute", "walked")),
    ("commute_work_from_home", ("commute", "work_from_home")),
    # Housing structure
    ("housing_single_family", ("housing_structure", "single_family")),
    ("housing_small_multifamily", ("housing_structure", "small_multifamily_2_9")),
    ("housing_large_multifamily", ("housing_structure", "large_multifamily_10plus")),
    ("housing_mobile_home", ("housing_structure", "mobile_home")),
    # Employment
    ("employment_employed", ("employment", "employed")),
    ("employment_unemployed", ("employment", "unemployed")),
    ("employment_not_in_labor_force", ("employment", "not_in_labor_force")),
    # School enrollment
    ("school_k12", ("school_enrollment", "k12")),
    ("school_college_undergrad", ("school_enrollment", "college_undergrad")),
    ("school_graduate_professional", ("school_enrollment", "graduate_professional")),
    ("school_not_enrolled", ("school_enrollment", "not_enrolled")),
    # SNAP
    ("snap_receiving", ("snap_assistance", "receiving")),
    ("snap_total_households", ("snap_assistance", "total_households")),
    # Rent burden
    ("rent_burden_30_plus", ("rent_burden", "burdened_30_plus_pct")),
    ("rent_burden_50_plus", ("rent_burden", "severely_burdened_50_plus_pct")),
    ("rent_burden_total", ("rent_burden", "renters_with_cash_rent")),
    # Mobility
    ("mobility_same_house", ("mobility", "same_house_year_ago")),
    ("mobility_moved_within_county", ("mobility", "moved_within_county")),
    ("mobility_moved_within_state", ("mobility", "moved_within_state")),
    ("mobility_moved_from_other_state", ("mobility", "moved_from_other_state")),
    ("mobility_moved_from_abroad", ("mobility", "moved_from_abroad")),
    # Language
    ("lang_english_only", ("language_at_home", "english_only")),
    ("lang_spanish", ("language_at_home", "spanish")),
    ("lang_other_indo_european", ("language_at_home", "other_indo_european")),
    ("lang_asian_pacific_islander", ("language_at_home", "asian_pacific_islander")),
    ("lang_other", ("language_at_home", "other")),
    # Occupation
    ("occ_management_business_science_arts", ("occupation", "management_business_science_arts")),
    ("occ_service", ("occupation", "service")),
    ("occ_sales_office", ("occupation", "sales_office")),
    ("occ_natural_resources_construction_maintenance", ("occupation", "natural_resources_construction_maintenance")),
    ("occ_production_transportation_material_moving", ("occupation", "production_transportation_material_moving")),
]

# Per-election precinct paths. We apply the same template to each election file
# and produce keys prefixed by the election (e.g. g24_reg_democratic, g22_top_race_democratic).
PER_ELECTION_TEMPLATE = [
    ("total_registered", ("total_registered",)),
    ("total_votes", ("total_votes",)),
    ("reg_democratic", ("registration", "democratic")),
    ("reg_republican", ("registration", "republican")),
    ("reg_no_party_preference", ("registration", "no_party_preference")),
    ("reg_american_independent", ("registration", "american_independent")),
    ("reg_libertarian", ("registration", "libertarian")),
    ("reg_green", ("registration", "green")),
    ("reg_peace_and_freedom", ("registration", "peace_and_freedom")),
    ("reg_other", ("registration", "other")),
    ("top_race_democratic", ("top_race", "democratic")),
    ("top_race_republican", ("top_race", "republican")),
    ("top_race_libertarian", ("top_race", "libertarian")),
    ("top_race_green", ("top_race", "green")),
    ("top_race_peace_and_freedom", ("top_race", "peace_and_freedom")),
    ("top_race_american_independent", ("top_race", "american_independent")),
    ("sen_democratic", ("senate", "democratic")),
    ("sen_republican", ("senate", "republican")),
]

ELECTIONS_TO_LOAD = ["g24", "g22"]


def deep_get(d: dict, path: tuple) -> float:
    for k in path:
        if d is None:
            return 0
        d = d.get(k, 0)
    try:
        return float(d)
    except (TypeError, ValueError):
        return 0


FEC_PARTY_KEYS = ("DEM", "REP", "LIB", "GRE", "IND", "OTHER")


def aggregate_polygon(
    polygon,
    bg_gdf: gpd.GeoDataFrame,
    demographics: dict,
    precinct_gdfs: dict[str, gpd.GeoDataFrame],
    zcta_gdf: gpd.GeoDataFrame | None = None,
    fec_data: dict | None = None,
) -> dict:
    """Areal-weighted aggregation of BG demographics + per-election precinct voter data."""
    aggregated: dict[str, float] = defaultdict(float)
    bg_ids_used: list[str] = []
    precincts_used_by_election: dict[str, list[str]] = {e: [] for e in precinct_gdfs}

    if polygon is None or polygon.is_empty:
        result = {k: 0 for k, _ in COUNT_PATHS}
        for election in ELECTIONS_TO_LOAD:
            for k, _ in PER_ELECTION_TEMPLATE:
                result[f"{election}_{k}"] = 0
        result |= {"catchment_area_acres": 0.0, "bg_intersect_count": 0}
        for e in precinct_gdfs:
            result[f"{e}_precinct_intersect_count"] = 0
        return result

    candidate_bgs = bg_gdf[bg_gdf.geometry.intersects(polygon)]
    for _, bg_row in candidate_bgs.iterrows():
        intersect_area = bg_row.geometry.intersection(polygon).area
        if intersect_area <= 0:
            continue
        weight = min(intersect_area / bg_row["bg_area_ft2"], 1.0)
        bg_data = demographics.get(bg_row["GEOID"])
        if not bg_data:
            continue
        bg_ids_used.append(bg_row["GEOID"])
        for out_key, path in COUNT_PATHS:
            aggregated[out_key] += deep_get(bg_data, path) * weight

    for election, gdf in precinct_gdfs.items():
        candidate_precincts = gdf[gdf.geometry.intersects(polygon)]
        for _, prec in candidate_precincts.iterrows():
            intersect_area = prec.geometry.intersection(polygon).area
            if intersect_area <= 0:
                continue
            weight = min(intersect_area / prec["precinct_area_ft2"], 1.0)
            prec_data = {
                "total_registered": prec["total_registered"],
                "total_votes": prec["total_votes"],
                "registration": prec["registration"],
                "top_race": prec["top_race"],
                "senate": prec["senate"],
            }
            precincts_used_by_election[election].append(str(prec["srprec"]))
            for out_key, path in PER_ELECTION_TEMPLATE:
                aggregated[f"{election}_{out_key}"] += deep_get(prec_data, path) * weight

    # FEC partisan donations — areal-weighted from ZCTA polygons.
    zctas_used: list[str] = []
    if zcta_gdf is not None and fec_data is not None:
        candidate_zctas = zcta_gdf[zcta_gdf.geometry.intersects(polygon)]
        for _, zr in candidate_zctas.iterrows():
            intersect_area = zr.geometry.intersection(polygon).area
            if intersect_area <= 0:
                continue
            weight = min(intersect_area / zr["zcta_area_ft2"], 1.0)
            zip5 = zr["zip5"]
            fec_entry = fec_data.get(zip5)
            if not fec_entry:
                continue
            zctas_used.append(zip5)
            aggregated["fec_donor_count"] += fec_entry["donor_count"] * weight
            aggregated["fec_total_amount"] += fec_entry["total_amount"] * weight
            for party in FEC_PARTY_KEYS:
                pdata = fec_entry["by_party"].get(party, {"amount": 0, "donor_count": 0})
                aggregated[f"fec_{party.lower()}_amount"] += pdata["amount"] * weight
                aggregated[f"fec_{party.lower()}_donor_count"] += pdata["donor_count"] * weight

    result = {k: round(v) for k, v in aggregated.items()}
    for out_key, _ in COUNT_PATHS:
        result.setdefault(out_key, 0)
    for election in ELECTIONS_TO_LOAD:
        for k, _ in PER_ELECTION_TEMPLATE:
            result.setdefault(f"{election}_{k}", 0)
    for party in FEC_PARTY_KEYS:
        result.setdefault(f"fec_{party.lower()}_amount", 0)
        result.setdefault(f"fec_{party.lower()}_donor_count", 0)
    result.setdefault("fec_donor_count", 0)
    result.setdefault("fec_total_amount", 0)
    result["catchment_area_acres"] = round(polygon.area / 43560, 1)
    result["bg_intersect_count"] = len(bg_ids_used)
    result["fec_zcta_intersect_count"] = len(zctas_used)
    for e in precinct_gdfs:
        result[f"{e}_precinct_intersect_count"] = len(precincts_used_by_election[e])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int)
    args = parser.parse_args()

    catchments_path = district_dir(args.district) / "catchments.geojson"
    if not catchments_path.exists():
        print(f"catchments.geojson not found. Run compute-catchments.py first.", file=sys.stderr)
        return 1

    boundary_path = district_dir(args.district) / "district-boundary.geojson"
    if not boundary_path.exists():
        print(f"district-boundary.geojson not found.", file=sys.stderr)
        return 1
    district_gdf = gpd.read_file(boundary_path).to_crs(epsg=2226)
    district_poly = district_gdf.geometry.iloc[0]

    demographics = load_demographics()
    print(f"Loaded ACS demographics for {len(demographics)} block groups")

    bg_gdf = load_or_fetch_bg_polygons().to_crs(epsg=2226)
    bg_gdf["bg_area_ft2"] = bg_gdf.geometry.area
    print(f"BG polygons projected to EPSG:2226 (CA State Plane, feet)")

    precinct_gdfs: dict[str, gpd.GeoDataFrame] = {}
    for election in ELECTIONS_TO_LOAD:
        g = load_or_fetch_precincts(election)
        if g is not None:
            precinct_gdfs[election] = g
            print(f"Loaded {len(g)} SWDB {election} precincts with voter data")
    if not precinct_gdfs:
        print("No precinct voter data found — political sections will be zero")

    zcta_gdf, fec_data = load_or_fetch_fec_zctas()
    if zcta_gdf is not None:
        print(f"Loaded {len(zcta_gdf)} ZCTAs with FEC partisan donor data")

    catchments_gdf = gpd.read_file(catchments_path)
    full_catchments = catchments_gdf[catchments_gdf["feature_type"] == "full"].to_crs(epsg=2226).copy()
    print(
        f"Aggregating {len(full_catchments)} full catchments × BG intersections "
        f"(both total + clipped-to-D{args.district})..."
    )

    results: dict[str, dict[str, dict]] = defaultdict(dict)
    for _, catchment in full_catchments.iterrows():
        venue_id = catchment["venue_id"]
        profile = catchment["profile"]
        catchment_poly = catchment.geometry
        in_district_poly = catchment_poly.intersection(district_poly)

        total = aggregate_polygon(catchment_poly, bg_gdf, demographics, precinct_gdfs, zcta_gdf, fec_data)
        in_district = aggregate_polygon(in_district_poly, bg_gdf, demographics, precinct_gdfs, zcta_gdf, fec_data)

        results[venue_id][profile] = {
            "total": total,
            "in_district": in_district,
        }

    # Final report shape: per venue, with profile sub-keys + venue metadata for reference.
    venue_meta = {
        f["properties"]["venue_id"]: {
            "venue_name": f["properties"]["venue_name"],
            "in_district_venue": f["properties"]["in_district_venue"],
        }
        for _, f in full_catchments[["venue_id", "venue_name", "in_district_venue"]]
        .drop_duplicates(subset="venue_id")
        .iterrows()
        for f in [{"properties": {
            "venue_id": f["venue_id"],
            "venue_name": f["venue_name"],
            "in_district_venue": f["in_district_venue"],
        }}]
    }
    output = {
        "generated": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "district": args.district,
        "data_source_note": (
            "Counts are areal-weighted aggregations of ACS 5-year 2023 block-group "
            "demographics intersected with the venue's walking/biking isochrone. "
            "Each catchment has two stat sets: 'total' = everyone in the catchment "
            f"polygon regardless of district; 'in_district' = only the slice that "
            f"falls inside the District {args.district} boundary (the audience the "
            "candidate can actually win as constituents). "
            "citizen_voting_age_population is estimated from each parent tract's "
            "CVAP rate × the BG's adult population (B05003 is suppressed at BG level)."
        ),
        "venues": {
            venue_id: {
                **venue_meta.get(venue_id, {}),
                "catchments": profiles,
            }
            for venue_id, profiles in results.items()
        },
    }

    out_path = district_dir(args.district) / "catchment-demographics.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nWrote {out_path} ({out_path.stat().st_size:,} bytes; {len(results)} venues)")

    # Quick spot-check: print one in-district + one adjacency venue's walk_15 numbers
    samples_shown = 0
    seen = {"in_district": False, "adjacency": False}
    for venue_id, venue in output["venues"].items():
        kind = "in_district" if venue.get("in_district_venue") else "adjacency"
        if seen[kind] or "walk_15" not in venue["catchments"]:
            continue
        seen[kind] = True
        bands = venue["catchments"]["walk_15"]
        total = bands["total"]
        ind = bands["in_district"]
        print(f"\nSample ({kind} venue '{venue['venue_name']}' walk_15):")
        print(f"  Catchment area:   {total['catchment_area_acres']:.0f} ac (in D{args.district}: {ind['catchment_area_acres']:.0f} ac)")
        print(f"  Est. residents:   {total['total_population']:,} total, {ind['total_population']:,} in D{args.district}")
        print(f"  Est. CVAP:        {total['citizen_voting_age_population']:,} total, {ind['citizen_voting_age_population']:,} in D{args.district}")
        samples_shown += 1
        if samples_shown >= 2:
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
