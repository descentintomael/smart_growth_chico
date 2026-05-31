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
import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.ops import unary_union

CHICO_GIS_ROOT = Path(
    "/Users/seantodd/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
    "Smart Growth Advocates/resources/chico-data/gis"
)
SOURCE_SHP = CHICO_GIS_ROOT / "precincts" / "CITYOFCHICOVOTINGDISTRICTS.shp"
ANNEXATIONS_SHP = CHICO_GIS_ROOT / "boundaries" / "CITYOFCHICOANNEXATIONBOUNDARIES.shp"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEEP_FIELDS = ["DISTRICT", "NAME"]


def load_annexation_polygons(annex_ids: list[int]) -> gpd.GeoDataFrame:
    """Load specific annexation polygons by their new_annex_ ID."""
    gdf = gpd.read_file(ANNEXATIONS_SHP)
    subset = gdf[gdf["new_annex_"].isin(annex_ids)].copy()
    missing = set(annex_ids) - set(subset["new_annex_"].astype(int))
    if missing:
        raise ValueError(f"Annexation IDs not found in shapefile: {missing}")
    return subset


def process(district: int, add_annex_ids: list[int] | None = None) -> tuple[Path, dict]:
    if not SOURCE_SHP.exists():
        raise FileNotFoundError(f"Source shapefile not found: {SOURCE_SHP}")

    gdf = gpd.read_file(SOURCE_SHP)
    match = gdf[gdf["DISTRICT"].astype(str) == str(district)]
    if match.empty:
        raise ValueError(f"District {district} not found in shapefile")

    cleaned = match[KEEP_FIELDS + ["geometry"]].copy().to_crs(epsg=4326)

    metadata: dict = {
        "district": district,
        "base_source": str(SOURCE_SHP),
        "augmentations": [],
    }

    if add_annex_ids:
        annex = load_annexation_polygons(add_annex_ids).to_crs(epsg=4326)
        merged_geom = unary_union([cleaned.geometry.iloc[0]] + list(annex.geometry))
        cleaned = cleaned.copy()
        cleaned.loc[cleaned.index[0], "geometry"] = merged_geom
        for _, row in annex.iterrows():
            metadata["augmentations"].append({
                "annex_id": int(row["new_annex_"]),
                "name": row["annexati_1"],
                "council_adopted": str(row.get("date_adopt")) if row.get("date_adopt") else None,
                "gis_updated": str(row.get("updated")) if row.get("updated") else None,
                "acres": float(row["acres"]),
                "note": "Unioned into district polygon to reflect annexation that the published voting districts shapefile does not yet show.",
            })

    out_dir = PROJECT_ROOT / "public" / "data" / f"candidate-district-{district}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "district-boundary.geojson"
    cleaned.to_file(out_path, driver="GeoJSON")
    (out_dir / "district-boundary.metadata.json").write_text(json.dumps(metadata, indent=2))
    return out_path, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="District number (1-7)")
    parser.add_argument(
        "--add-annex",
        type=int,
        nargs="*",
        default=[],
        help="One or more annexation new_annex_ IDs to union into the district polygon.",
    )
    args = parser.parse_args()

    out, meta = process(args.district, add_annex_ids=args.add_annex or None)
    print(f"Wrote {out} ({out.stat().st_size:,} bytes)")
    if meta["augmentations"]:
        print(f"Applied {len(meta['augmentations'])} annexation augmentation(s):")
        for aug in meta["augmentations"]:
            print(f"  - {aug['name']} ({aug['acres']:.1f} ac, adopted {aug['council_adopted']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
