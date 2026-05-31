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
from shapely.geometry.base import BaseGeometry

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
    "golf_course",
    "dance",
    "bowling_alley",
]
TOURISM_VALUES = ["hotel", "motel", "gallery", "museum"]
SHOP_VALUES = ["books"]  # Big-box alcohol retail dropped — almost never hosts events
CRAFT_VALUES = ["brewery", "winery", "distillery"]
OFFICE_VALUES = ["coworking"]

# Categorical hard-excludes: these venue types fundamentally don't host political events.
HARD_EXCLUDE_AMENITY = {
    "place_of_worship",
    "monastery",
    "fast_food",       # Quick-service; no rentable space
    "kindergarten",    # Preschools
    "childcare",       # Daycares
}
# K-12 schools (amenity=school) are kept. Public school auditoriums can sometimes be
# booked for civic events with district approval. Preschools mis-tagged as
# amenity=school are filtered out by NAME_EXCLUDE_SUBSTRINGS below.

HARD_EXCLUDE_LEISURE = {
    "fitness_centre",  # Gyms (Planet Fitness etc.)
    "sports_centre",   # Gyms/sports facilities — drop by default
}

# Substrings in the venue name that indicate the venue is a preschool / daycare /
# auto-care business mis-tagged or otherwise inappropriate.
NAME_EXCLUDE_SUBSTRINGS = [
    "preschool", "pre-school", "day care", "daycare", "child care", "childcare",
    "academy of dance", "kids care",
]

# Fraternal / civic order brand names that look like chains in OSM but are actually
# federations of independently-operated local chapters. These regularly host civic
# events including candidate forums, and should NOT be auto-excluded as chains.
FRATERNAL_BRAND_PATTERNS = [
    "Elks", "Moose", "Eagles", "Lions", "Masons", "Masonic",
    "American Legion", "Veterans of Foreign Wars", "VFW",
    "Optimist", "Rotary", "Kiwanis", "Knights of Columbus",
    "Odd Fellows", "Order of",
]

# Backup chain-name list for chains that OSM didn't tag with a `brand` key.
CHAIN_EXCLUDE_NAMES = {
    # Restaurant chains the user has explicitly flagged or that are clearly national
    "Logans", "Logan's Roadhouse",
    # Other large chains seen in NorCal where the brand tag may be missing
    "Burrito Bandito", "Panera Bread", "Olive Garden", "Red Lobster",
    "Applebee's", "Chili's", "Black Bear Diner",
    "McDonald's", "Subway", "Taco Bell", "Pizza Hut", "Domino's",
    "KFC", "Wendy's", "In-N-Out Burger", "Carl's Jr.", "Chick-fil-A",
    "Jack in the Box", "Round Table Pizza", "Panda Express", "Chipotle",
    "Starbucks",
    # Hotel chains
    "Holiday Inn Express", "Best Western", "Motel 6", "Super 8",
    "Days Inn", "Comfort Inn", "Hampton Inn", "Hampton Inn & Suites", "La Quinta",
    "Oxford Suites Chico",  # Regional chain
    # Big-box retail
    "BevMo!", "Walmart", "Target", "Costco", "Sam's Club",
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


def classify_exclusion(tags: dict, name: str) -> str | None:
    """Return a human-readable reason if this venue should be excluded, else None."""
    amenity = tags.get("amenity")
    leisure = tags.get("leisure")
    club = tags.get("club")
    brand = tags.get("brand") or tags.get("brand:wikidata")

    if amenity in HARD_EXCLUDE_AMENITY:
        return f"category not suitable for hosting events (amenity={amenity})"
    if leisure in HARD_EXCLUDE_LEISURE:
        return f"category not suitable for hosting events (leisure={leisure})"
    if tags.get("religion") or tags.get("denomination") or club == "religion":
        return "religious site (excluded per maintainer policy unless explicit confirmation)"
    if brand:
        # Fraternal orders look like chains but each local chapter is independent and
        # often hosts civic events — don't auto-exclude.
        if not any(p.lower() in brand.lower() for p in FRATERNAL_BRAND_PATTERNS):
            return f"chain venue (OSM brand={brand!r}); chains rarely book candidate events"
    name_lower = name.lower()
    for sub in NAME_EXCLUDE_SUBSTRINGS:
        if sub in name_lower:
            return f"name contains {sub!r} (likely preschool/daycare/inappropriate)"
    if name in CHAIN_EXCLUDE_NAMES:
        return "known chain (backup name match)"
    return None


def element_to_feature(elem: dict, excluded_log: list) -> dict | None:
    tags = elem.get("tags", {})
    amenity = tags.get("amenity")
    leisure = tags.get("leisure")
    tourism = tags.get("tourism")
    shop = tags.get("shop")
    craft = tags.get("craft")
    office = tags.get("office")
    club = tags.get("club")

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

    reason = classify_exclusion(tags, name)
    if reason:
        excluded_log.append({
            "osm_id": f"{elem['type']}/{elem['id']}",
            "name": name,
            "reason": reason,
            "amenity": amenity,
            "leisure": leisure,
            "tourism": tourism,
            "club": club,
            "brand": tags.get("brand"),
        })
        return None

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
    if (amenity == "school") or (tourism in ("hotel", "motel")):
        notes = (
            "Public school auditoriums and hotel meeting rooms typically require an "
            "explicit booking arrangement — confirm with the venue before assuming."
            if amenity == "school"
            else "Hotel meeting rooms vary widely in price and political-event policy — "
                 "confirm with sales team."
        )

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


def buffer_polygon(poly_4326: BaseGeometry, miles: float) -> BaseGeometry:
    """Buffer a WGS84 polygon by `miles` (using California State Plane for accuracy)."""
    series = gpd.GeoSeries([poly_4326], crs="EPSG:4326").to_crs(epsg=2226)
    buffered_ft = series.iloc[0].buffer(miles * 5280.0)
    return gpd.GeoSeries([buffered_ft], crs="EPSG:2226").to_crs(epsg=4326).iloc[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="District number")
    parser.add_argument(
        "--buffer-miles",
        type=float,
        default=0.0,
        help="Include venues in adjacent districts whose walking catchment could "
             "plausibly reach district residents (default 0.0 = strict in-district only; "
             "1.0 captures the upper bound of a 15-minute walk).",
    )
    args = parser.parse_args()

    boundary = gpd.read_file(boundary_path(args.district))
    if boundary.crs is None or boundary.crs.to_epsg() != 4326:
        boundary = boundary.to_crs(epsg=4326)
    district_poly = boundary.geometry.iloc[0]

    spatial_poly = district_poly
    if args.buffer_miles > 0:
        spatial_poly = buffer_polygon(district_poly, args.buffer_miles)
        print(f"Buffering district by {args.buffer_miles} mi for spatial filter.")

    west, south, east, north = spatial_poly.bounds
    print(f"Spatial bbox: W={west:.5f} S={south:.5f} E={east:.5f} N={north:.5f}")

    query = build_query(west, south, east, north)
    print("Querying Overpass...")
    t0 = time.time()
    payload = query_overpass(query)
    print(f"  Returned {len(payload.get('elements', []))} elements in {time.time() - t0:.1f}s")

    features = []
    excluded_log: list = []
    for elem in payload.get("elements", []):
        feature = element_to_feature(elem, excluded_log)
        if feature:
            features.append(feature)
    print(f"  Kept {len(features)} viable features after filtering")
    print(f"  Excluded {len(excluded_log)} (audit log written to excluded.json)")

    inside = []
    in_district_count = 0
    adjacency_count = 0
    for feature in features:
        lon, lat = feature["geometry"]["coordinates"]
        pt = Point(lon, lat)
        if not spatial_poly.contains(pt):
            continue
        in_district = district_poly.contains(pt)
        feature["properties"]["in_district"] = in_district
        if in_district:
            in_district_count += 1
        else:
            adjacency_count += 1
        inside.append(feature)
    print(f"  {in_district_count} venues inside District {args.district}")
    print(f"  {adjacency_count} venues in adjacency buffer (outside D{args.district} but within {args.buffer_miles} mi)")

    out_dir = boundary_path(args.district).parent
    out_path = out_dir / "venues.geojson"
    fc = {"type": "FeatureCollection", "features": inside}
    out_path.write_text(json.dumps(fc, indent=2))
    excluded_path = out_dir / "excluded.json"
    excluded_path.write_text(json.dumps({
        "note": "Venues removed during OSM-based filtering. Audit trail for which OSM "
                "features were dropped and why.",
        "count": len(excluded_log),
        "entries": excluded_log,
    }, indent=2))
    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    print(f"Wrote {excluded_path} ({excluded_path.stat().st_size:,} bytes)")

    counts: dict[str, int] = {}
    for f in inside:
        cat = f["properties"]["category"]
        bucket = cat if f["properties"]["in_district"] else f"{cat} (adjacency)"
        counts[bucket] = counts.get(bucket, 0) + 1
    print("\nViable venues by category:")
    for cat in sorted(counts, key=counts.get, reverse=True):
        print(f"  {counts[cat]:4d}  {cat}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
