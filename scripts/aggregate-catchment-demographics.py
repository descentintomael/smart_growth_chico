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
]


def deep_get(d: dict, path: tuple) -> float:
    for k in path:
        if d is None:
            return 0
        d = d.get(k, 0)
    try:
        return float(d)
    except (TypeError, ValueError):
        return 0


def aggregate_polygon(
    polygon, bg_gdf: gpd.GeoDataFrame, demographics: dict
) -> dict:
    """Areal-weighted aggregation of BG demographics within a single polygon."""
    aggregated: dict[str, float] = defaultdict(float)
    bg_ids_used: list[str] = []

    if polygon is None or polygon.is_empty:
        return {k: 0 for _, (k, _) in enumerate(COUNT_PATHS)} | {
            "catchment_area_acres": 0.0,
            "bg_intersect_count": 0,
        }

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

    result = {k: round(v) for k, v in aggregated.items()}
    for out_key, _ in COUNT_PATHS:
        result.setdefault(out_key, 0)
    result["catchment_area_acres"] = round(polygon.area / 43560, 1)
    result["bg_intersect_count"] = len(bg_ids_used)
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

        total = aggregate_polygon(catchment_poly, bg_gdf, demographics)
        in_district = aggregate_polygon(in_district_poly, bg_gdf, demographics)

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
