#!/usr/bin/env python3
"""Fetch candidate-event venues from OpenStreetMap via the Overpass API.

Queries OSM for amenities likely to host political events (libraries, community
centers, bars, cafes, restaurants, pubs, theatres, arts venues, colleges) within
the bounding box of a given council district, spatially clips to the district
polygon, applies the maintainer's exclusion rules (churches, religious sites),
and writes a GeoJSON point dataset.

This produces an initial dump only. Capacity, accessibility, and political-event
hosting policy must still be researched per venue and recorded separately.

Usage:
    python3 scripts/fetch-venues-overpass.py 6
"""

import argparse
import json
import sys
import time
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import Point

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Amenity / leisure values we want to pull in
AMENITY_VALUES = [
    "library",
    "community_centre",
    "cafe",
    "restaurant",
    "bar",
    "pub",
    "biergarten",
    "theatre",
    "cinema",
    "arts_centre",
    "college",
    "university",
    "events_venue",
    "conference_centre",
    "social_centre",
    "school",
    "social_facility",
    "townhall",
    "marketplace",
    "music_venue",
    "nightclub",
    "casino",
    "clubhouse",
]
LEISURE_VALUES = [
    "community_centre",
    "sports_centre",
    "golf_course",
    "fitness_centre",
    "dance",
    "bowling_alley",
    "recreation_ground",
]
TOURISM_VALUES = ["hotel", "motel", "gallery", "museum"]
SHOP_VALUES = ["books", "alcohol", "wine"]
CRAFT_VALUES = ["brewery", "winery", "distillery"]
OFFICE_VALUES = ["coworking"]

# Known chains that effectively never host political events (auto-exclude on import).
# Kept conservative — only obvious national chains where a candidate booking is implausible.
CHAIN_EXCLUDE_NAMES = {
    "Starbucks", "Panera Bread", "Olive Garden", "Red Lobster",
    "Applebee's", "Chili's", "Black Bear Diner", "Burrito Bandito",
    "McDonald's", "Subway", "Taco Bell", "Pizza Hut", "Domino's",
    "KFC", "Wendy's", "In-N-Out Burger", "Carl's Jr.", "Chick-fil-A",
    "Jack in the Box", "Round Table Pizza", "Panda Express",
    "Holiday Inn Express", "Best Western", "Motel 6", "Super 8",
    "Days Inn", "Comfort Inn", "Hampton Inn", "La Quinta",
}

# Things we never want, even if Overpass returned them somehow
HARD_EXCLUDE_AMENITY = {"place_of_worship", "monastery"}


def boundary_path(district: int) -> Path:
    return PROJECT_ROOT / "public" / "data" / f"candidate-district-{district}" / "district-boundary.geojson"


def build_query(west: float, south: float, east: float, north: float) -> str:
    amenity_regex = "|".join(AMENITY_VALUES)
    leisure_regex = "|".join(LEISURE_VALUES)
    tourism_regex = "|".join(TOURISM_VALUES)
    shop_regex = "|".join(SHOP_VALUES)
    craft_regex = "|".join(CRAFT_VALUES)
    office_regex = "|".join(OFFICE_VALUES)
    bbox = f"{south},{west},{north},{east}"
    return f"""
[out:json][timeout:120];
(
  node["amenity"~"^({amenity_regex})$"]({bbox});
  way["amenity"~"^({amenity_regex})$"]({bbox});
  relation["amenity"~"^({amenity_regex})$"]({bbox});
  node["leisure"~"^({leisure_regex})$"]({bbox});
  way["leisure"~"^({leisure_regex})$"]({bbox});
  relation["leisure"~"^({leisure_regex})$"]({bbox});
  node["tourism"~"^({tourism_regex})$"]({bbox});
  way["tourism"~"^({tourism_regex})$"]({bbox});
  relation["tourism"~"^({tourism_regex})$"]({bbox});
  node["shop"~"^({shop_regex})$"]({bbox});
  way["shop"~"^({shop_regex})$"]({bbox});
  relation["shop"~"^({shop_regex})$"]({bbox});
  node["craft"~"^({craft_regex})$"]({bbox});
  way["craft"~"^({craft_regex})$"]({bbox});
  relation["craft"~"^({craft_regex})$"]({bbox});
  node["office"~"^({office_regex})$"]({bbox});
  way["office"~"^({office_regex})$"]({bbox});
  relation["office"~"^({office_regex})$"]({bbox});
  node["club"]({bbox});
  way["club"]({bbox});
  relation["club"]({bbox});
);
out center tags;
""".strip()


def query_overpass(query: str) -> dict:
    headers = {
        "User-Agent": "smart-growth-visualizer/0.1 candidate-venue-research (local research, contact via repo)",
        "Accept": "application/json",
    }
    response = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=120)
    response.raise_for_status()
    return response.json()


def element_to_feature(elem: dict) -> dict | None:
    tags = elem.get("tags", {})
    amenity = tags.get("amenity")
    leisure = tags.get("leisure")
    tourism = tags.get("tourism")
    shop = tags.get("shop")
    craft = tags.get("craft")
    office = tags.get("office")
    club = tags.get("club")
    if amenity in HARD_EXCLUDE_AMENITY:
        return None
    # Religious markers anywhere → out (covers churches, religious clubs, Masonic temples
    # that explicitly self-tag as religious, etc.)
    if tags.get("religion") or tags.get("denomination") or club == "religion":
        return None

    if elem["type"] == "node":
        lon, lat = elem.get("lon"), elem.get("lat")
    else:
        center = elem.get("center") or {}
        lon, lat = center.get("lon"), center.get("lat")
    if lon is None or lat is None:
        return None

    name = tags.get("name")
    if not name:
        return None  # unnamed venues are not usable for outreach

    addr_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:city"),
    ]
    address = " ".join(p for p in addr_parts if p) or None

    # Prefer the most specific tag for category. craft/club tags often layer on top of
    # an amenity (e.g., Sierra Nevada is both amenity=pub and craft=brewery).
    if craft:
        category = f"craft_{craft}"
    elif club:
        category = f"club_{club}"
    elif tourism:
        category = f"tourism_{tourism}"
    elif office:
        category = f"office_{office}"
    elif shop:
        category = f"shop_{shop}"
    else:
        category = amenity or leisure or "other"

    hosting_status = "needs_verification"
    notes = None
    if name in CHAIN_EXCLUDE_NAMES:
        hosting_status = "excluded"
        notes = "Auto-excluded: national chain unlikely to host political events"

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "osm_id": f"{elem['type']}/{elem['id']}",
            "name": name,
            "category": category,
            "amenity": amenity,
            "leisure": leisure,
            "tourism": tourism,
            "shop": shop,
            "craft": craft,
            "office": office,
            "club": club,
            "address": address,
            "website": tags.get("website") or tags.get("contact:website"),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "capacity": tags.get("capacity") or tags.get("capacity:persons"),
            "wheelchair": tags.get("wheelchair"),
            "operator": tags.get("operator"),
            "hosting_status": hosting_status,
            "notes": notes,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="District number")
    args = parser.parse_args()

    boundary = gpd.read_file(boundary_path(args.district))
    if boundary.crs is None or boundary.crs.to_epsg() != 4326:
        boundary = boundary.to_crs(epsg=4326)
    west, south, east, north = boundary.total_bounds
    print(f"District {args.district} bbox: W={west:.5f} S={south:.5f} E={east:.5f} N={north:.5f}")

    query = build_query(west, south, east, north)
    print("Querying Overpass...")
    t0 = time.time()
    payload = query_overpass(query)
    print(f"  Returned {len(payload.get('elements', []))} elements in {time.time() - t0:.1f}s")

    features = []
    for elem in payload.get("elements", []):
        feature = element_to_feature(elem)
        if feature:
            features.append(feature)
    print(f"  Kept {len(features)} named, non-religious features")

    # Spatial filter against the actual district polygon
    district_poly = boundary.geometry.iloc[0]
    inside = []
    for feature in features:
        lon, lat = feature["geometry"]["coordinates"]
        if district_poly.contains(Point(lon, lat)):
            inside.append(feature)
    print(f"  {len(inside)} fall inside the District {args.district} polygon")

    out_dir = boundary_path(args.district).parent
    out_path = out_dir / "venues.geojson"
    fc = {"type": "FeatureCollection", "features": inside}
    out_path.write_text(json.dumps(fc, indent=2))
    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")

    # Quick category breakdown
    counts: dict[str, int] = {}
    for f in inside:
        counts[f["properties"]["category"]] = counts.get(f["properties"]["category"], 0) + 1
    for cat in sorted(counts, key=counts.get, reverse=True):
        print(f"  {counts[cat]:4d}  {cat}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
