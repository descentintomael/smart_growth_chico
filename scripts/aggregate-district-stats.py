#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.32",
#     "shapely>=2.0",
#     "pyproj>=3.6",
# ]
# ///
"""Aggregate district-level demographics + local-business counts for the print poster.

  * Demographics: area-weighted spatial join of Butte County block groups
    (cached at .cache/tiger/butte-bg-polygons.geojson) with their ACS
    fields (public/data/_shared/butte-bg-acs.json).
  * Businesses: an Overpass query for amenity/shop/craft/tourism POIs
    in the district bbox, point-in-polygon-filtered to the boundary.

Output: public/data/candidate-district-N/print-district-stats.json with
a shape designed for direct consumption by the print SVG renderer.

Usage:
    scripts/aggregate-district-stats.py 6
"""
import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests
from pyproj import Transformer
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform as shapely_transform, unary_union

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BG_GEOJSON = PROJECT_ROOT / ".cache" / "tiger" / "butte-bg-polygons.geojson"
ACS_JSON = PROJECT_ROOT / "_shared_or_root_only"
ACS_JSON = PROJECT_ROOT / "public" / "data" / "_shared" / "butte-bg-acs.json"

WGS84_TO_UTM = Transformer.from_crs(
    "EPSG:4326", "EPSG:32610", always_xy=True
).transform


# ------------------------- Demographics aggregation -------------------------

# Category buckets used in the output. Each maps an OSM amenity/shop/craft/
# tourism value to a public-facing category label. Values *not* listed here
# get bucketed into "Other" (and dropped).
BUSINESS_BUCKETS = {
    "amenity:restaurant":  "food_and_drink",
    "amenity:fast_food":   "food_and_drink",
    "amenity:cafe":        "food_and_drink",
    "amenity:bar":         "food_and_drink",
    "amenity:pub":         "food_and_drink",
    "amenity:biergarten":  "food_and_drink",
    "amenity:food_court":  "food_and_drink",
    "amenity:ice_cream":   "food_and_drink",
    "craft:brewery":       "food_and_drink",
    "craft:winery":        "food_and_drink",
    "craft:distillery":    "food_and_drink",
    "shop:supermarket":    "grocery",
    "shop:convenience":    "grocery",
    "shop:greengrocer":    "grocery",
    "shop:bakery":         "grocery",
    "amenity:hospital":    "medical",
    "amenity:clinic":      "medical",
    "amenity:doctors":     "medical",
    "amenity:dentist":     "medical",
    "amenity:pharmacy":    "medical",
    "amenity:veterinary":  "medical",
    "amenity:school":      "schools",
    "amenity:university":  "schools",
    "amenity:college":     "schools",
    "amenity:kindergarten": "schools",
    "amenity:library":     "civic",
    "amenity:fire_station": "civic",
    "amenity:police":      "civic",
    "amenity:townhall":    "civic",
    "amenity:post_office": "civic",
    "amenity:community_centre": "civic",
    "tourism:hotel":       "hospitality",
    "tourism:motel":       "hospitality",
    "tourism:museum":      "cultural",
    "tourism:gallery":     "cultural",
    "amenity:theatre":     "cultural",
    "amenity:cinema":      "cultural",
    "amenity:arts_centre": "cultural",
}


def overpass_business_query(s, w, n, e) -> str:
    """All amenity/shop/craft/tourism POIs in the bbox — nodes + ways."""
    bbox = f"{s},{w},{n},{e}"
    return f"""
[out:json][timeout:240];
(
  node["amenity"]({bbox});
  way["amenity"]({bbox});
  node["shop"]({bbox});
  way["shop"]({bbox});
  node["craft"]({bbox});
  way["craft"]({bbox});
  node["tourism"]({bbox});
  way["tourism"]({bbox});
);
out center tags;
""".strip()


def fetch_overpass(query: str, cache_path: Path, force: bool = False) -> dict:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not force:
        print(f"[cache] reading {cache_path}", file=sys.stderr)
        return json.loads(cache_path.read_text())
    headers = {
        "User-Agent": "smart-growth-visualizer/0.1 district-stats (local research)",
        "Accept": "application/json",
    }
    print(f"[overpass] querying ({len(query)} bytes)…", file=sys.stderr)
    t0 = time.time()
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=400)
    resp.raise_for_status()
    payload = resp.json()
    dt = time.time() - t0
    print(
        f"[overpass] {len(payload.get('elements', []))} elements in {dt:.1f}s",
        file=sys.stderr,
    )
    cache_path.write_text(json.dumps(payload))
    return payload


def element_point(el) -> Point | None:
    """Best-effort representative point for an OSM element."""
    if el.get("type") == "node":
        return Point(el["lon"], el["lat"])
    center = el.get("center")
    if center:
        return Point(center["lon"], center["lat"])
    return None


def classify_business(tags: dict) -> str | None:
    for tag in ("amenity", "shop", "craft", "tourism"):
        v = tags.get(tag)
        if not v:
            continue
        key = f"{tag}:{v}"
        if key in BUSINESS_BUCKETS:
            return BUSINESS_BUCKETS[key]
        # Catch-all: any shop=* is retail
        if tag == "shop":
            return "retail"
    return None


def aggregate_businesses(payload: dict, district_wgs) -> dict:
    """Return {category: count} for businesses inside the district polygon."""
    counts = Counter()
    detailed = Counter()
    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        bucket = classify_business(tags)
        if bucket is None:
            continue
        pt = element_point(el)
        if pt is None:
            continue
        if not district_wgs.contains(pt):
            continue
        counts[bucket] += 1
        # Track the specific value for top-categories context
        for tag in ("amenity", "shop", "craft", "tourism"):
            if tag in tags:
                detailed[f"{tag}:{tags[tag]}"] += 1
                break
    return dict(counts), dict(detailed)


# ------------------------- ACS aggregation -------------------------

def load_district(boundary_path: Path):
    data = json.loads(boundary_path.read_text())
    return unary_union([shape(f["geometry"]) for f in data["features"]])


def aggregate_acs(district_utm, bg_geojson_path: Path, acs_path: Path) -> dict:
    bg_data = json.loads(bg_geojson_path.read_text())
    acs = json.loads(acs_path.read_text())["block_groups"]

    # Tally by area-weighted overlap
    pop_total = 0.0
    households_total = 0.0
    age_buckets = Counter()
    owner_units = 0.0
    renter_units = 0.0
    workers_total = 0.0
    commute_buckets = Counter()
    education_buckets = Counter()
    language_buckets = Counter()
    area_m2_total = 0.0
    bg_count = 0

    for feat in bg_data["features"]:
        geoid = feat["properties"].get("GEOID")
        if not geoid:
            continue
        bg_acs = acs.get(geoid)
        if not bg_acs:
            continue

        bg_wgs = shape(feat["geometry"])
        bg_utm = shapely_transform(WGS84_TO_UTM, bg_wgs)
        if not bg_utm.intersects(district_utm):
            continue

        # Fraction of the block group that lies inside the district.
        intersect = bg_utm.intersection(district_utm)
        if intersect.is_empty:
            continue
        frac = intersect.area / bg_utm.area
        if frac < 0.01:
            continue
        bg_count += 1

        # Area-weighted population
        pop = bg_acs.get("total_population", 0) or 0
        pop_total += pop * frac

        # Households
        income = bg_acs.get("household_income") or {}
        hh = income.get("total_households", 0) or 0
        households_total += hh * frac

        # Age distribution
        age = bg_acs.get("age") or {}
        for k, v in age.items():
            age_buckets[k] += (v or 0) * frac

        # Owner / renter
        tenure = bg_acs.get("tenure") or {}
        owner_units += (tenure.get("owner") or 0) * frac
        renter_units += (tenure.get("renter") or 0) * frac

        # Commute
        commute = bg_acs.get("commute") or {}
        workers = commute.get("total_workers", 0) or 0
        workers_total += workers * frac
        for k in ("drove_alone", "carpooled", "public_transit", "bicycle", "walked", "work_from_home"):
            commute_buckets[k] += (commute.get(k) or 0) * frac

        # Education
        edu = bg_acs.get("education_25plus") or {}
        for k in ("less_than_hs", "high_school", "some_college", "bachelors", "graduate"):
            education_buckets[k] += (edu.get(k) or 0) * frac

        # Language at home
        lang = bg_acs.get("language_at_home") or {}
        for k in ("english_only", "spanish", "other_indo_european", "asian_pacific_islander", "other"):
            language_buckets[k] += (lang.get(k) or 0) * frac

        area_m2_total += intersect.area

    # Area in square miles (1 sq mi = 2,589,988 m²)
    area_sq_mi = area_m2_total / 2_589_988

    return {
        "block_groups_included": bg_count,
        "population": round(pop_total),
        "households": round(households_total),
        "land_area_sq_mi": round(area_sq_mi, 2),
        "age": {k: round(v) for k, v in age_buckets.items()},
        "owner_occupied": round(owner_units),
        "renter_occupied": round(renter_units),
        "commute": {
            "total_workers": round(workers_total),
            **{k: round(v) for k, v in commute_buckets.items()},
        },
        "education_25plus": {k: round(v) for k, v in education_buckets.items()},
        "language_at_home": {k: round(v) for k, v in language_buckets.items()},
    }


# ------------------------- Main -------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args()

    base = PROJECT_ROOT / "public" / "data" / f"candidate-district-{args.district}"
    boundary_path = base / "district-boundary.geojson"
    out_path = base / "print-district-stats.json"
    cache_path = PROJECT_ROOT / ".cache" / "overpass" / f"district-{args.district}-businesses.json"

    if not boundary_path.exists():
        sys.exit(f"Boundary not found: {boundary_path}")
    if not BG_GEOJSON.exists():
        sys.exit(f"Block-group geometries not found: {BG_GEOJSON}")
    if not ACS_JSON.exists():
        sys.exit(f"ACS data not found: {ACS_JSON}")

    district_wgs = load_district(boundary_path)
    district_utm = shapely_transform(WGS84_TO_UTM, district_wgs)

    print(f"[district {args.district}] aggregating ACS over block groups…", file=sys.stderr)
    demographics = aggregate_acs(district_utm, BG_GEOJSON, ACS_JSON)

    print(f"[district {args.district}] fetching business POIs…", file=sys.stderr)
    minx, miny, maxx, maxy = district_wgs.bounds
    payload = fetch_overpass(
        overpass_business_query(miny, minx, maxy, maxx),
        cache_path,
        force=args.force_refresh,
    )
    business_counts, business_detail = aggregate_businesses(payload, district_wgs)

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "district": args.district,
        "demographics": demographics,
        "businesses": {
            "by_bucket": business_counts,
            "detailed": business_detail,
        },
    }
    out_path.write_text(json.dumps(out, indent=2))

    print(
        f"[out] wrote {out_path}\n"
        f"      population ≈ {demographics['population']:,}\n"
        f"      households ≈ {demographics['households']:,}\n"
        f"      area       ≈ {demographics['land_area_sq_mi']} sq mi\n"
        f"      businesses by bucket: {business_counts}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
