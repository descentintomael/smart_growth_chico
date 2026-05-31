#!/usr/bin/env python3
"""Process a Chico council district boundary into a clean GeoJSON.

Reads the City of Chico voting districts shapefile, filters to the requested
district number, strips personnel fields (incumbent name, email, term date) that
are irrelevant to catchment analysis, reprojects to EPSG:4326, and writes the
result to public/data/candidate-district-{N}/district-boundary.geojson.

Usage:
    python3 scripts/process-council-district.py 6
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd

SOURCE_SHP = Path(
    "/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
    "Smart Growth Advocates/resources/chico-data/gis/precincts/"
    "CITYOFCHICOVOTINGDISTRICTS.shp"
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEEP_FIELDS = ["DISTRICT", "NAME"]


def process(district: int) -> Path:
    if not SOURCE_SHP.exists():
        raise FileNotFoundError(f"Source shapefile not found: {SOURCE_SHP}")

    gdf = gpd.read_file(SOURCE_SHP)
    match = gdf[gdf["DISTRICT"].astype(str) == str(district)]
    if match.empty:
        raise ValueError(f"District {district} not found in shapefile")

    cleaned = match[KEEP_FIELDS + ["geometry"]].copy()
    cleaned = cleaned.to_crs(epsg=4326)

    out_dir = PROJECT_ROOT / "public" / "data" / f"candidate-district-{district}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "district-boundary.geojson"
    cleaned.to_file(out_path, driver="GeoJSON")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="District number (1-7)")
    args = parser.parse_args()

    out = process(args.district)
    print(f"Wrote {out} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
