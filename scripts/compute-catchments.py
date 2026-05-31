#!/usr/bin/env python3
"""Compute walking + biking catchment polygons for each venue.

For each venue in public/data/candidate-district-{N}/venues.geojson, computes
4 isochrone polygons against the OSM walk network: walk_10, walk_15,
bike_10, bike_15 (minutes).

Approach:
  1. Compute bbox of all venues + buffer (covers the max bike_15 reach).
  2. Download the OSM walk network for that bbox once (OSMnx).
  3. For each venue, find the nearest network node and compute an ego graph
     by edge length, sized to the (mode_speed × minutes) distance.
  4. Build a concave-hull polygon around the reached nodes, then buffer
     slightly so the shape captures parcels along the edge of the network.

Outputs: public/data/candidate-district-{N}/catchments.geojson
         (4 polygon features per venue with venue_id, mode, minutes).

Re-running re-uses the cached OSM graph at .cache/osm/network-{N}.graphml.

Usage:
    python3 scripts/compute-catchments.py 6
"""

import argparse
import json
import sys
import time
from pathlib import Path

import geopandas as gpd
import networkx as nx
import osmnx as ox
import shapely
from shapely.geometry import MultiPoint, Point, shape as shape_from_geom
from shapely.geometry.base import BaseGeometry

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Speeds in meters per minute (deliberately conservative — slow walkers, casual cyclists).
WALK_MPM = 80.5   # 3.0 mph
BIKE_MPM = 268.2  # 10.0 mph

# How far past the venue bbox we need to pull network data to cover bike_15 isochrones.
# 15 min × 268.2 m/min = ~4 km ≈ 2.5 mi. We pad to 3 mi to be safe.
NETWORK_BUFFER_MILES = 3.0

# Concave-hull tightness. 0 = tightest concave, 1 = convex hull. Lower = more honest
# but can produce slivers; tune with the rendered output in mind.
CONCAVE_RATIO = 0.25

# Buffer applied to the concave hull (in feet, then reprojected) so the catchment
# extends slightly beyond the road network — captures parcels adjacent to streets.
HULL_BUFFER_FT = 100.0  # ~30 m

PROFILES = [
    ("walk_10", "walk", 10, WALK_MPM),
    ("walk_15", "walk", 15, WALK_MPM),
    ("bike_10", "bike", 10, BIKE_MPM),
    ("bike_15", "bike", 15, BIKE_MPM),
]


def district_dir(n: int) -> Path:
    return PROJECT_ROOT / "public" / "data" / f"candidate-district-{n}"


def cache_dir() -> Path:
    d = PROJECT_ROOT / ".cache" / "osm"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_or_download_network(north, south, east, west, district: int):
    """Cache the OSM graph per-district so re-runs don't re-download."""
    cached_path = cache_dir() / f"network-d{district}.graphml"
    # Pin OSMnx's own cache to the same .cache/ tree so we don't spawn a
    # stray ./cache/ directory at the project root.
    ox.settings.cache_folder = str(cache_dir() / "osmnx-cache")
    if cached_path.exists():
        print(f"Loading cached OSM network from {cached_path}")
        return ox.load_graphml(str(cached_path))
    print(
        f"Downloading OSM walk network for bbox "
        f"W={west:.4f} S={south:.4f} E={east:.4f} N={north:.4f} ..."
    )
    t0 = time.time()
    # OSMnx 2.x bbox tuple format: (west, south, east, north)
    G = ox.graph_from_bbox(
        bbox=(west, south, east, north),
        network_type="walk",
        simplify=True,
    )
    print(f"  Downloaded {len(G.nodes)} nodes, {len(G.edges)} edges in {time.time() - t0:.1f}s")
    ox.save_graphml(G, str(cached_path))
    return G


def buffer_polygon_ft(poly_4326: BaseGeometry, feet: float) -> BaseGeometry:
    """Buffer a WGS84 polygon by `feet` using California State Plane (EPSG:2226)."""
    series = gpd.GeoSeries([poly_4326], crs="EPSG:4326").to_crs(epsg=2226)
    buffered = series.iloc[0].buffer(feet)
    return gpd.GeoSeries([buffered], crs="EPSG:2226").to_crs(epsg=4326).iloc[0]


def compute_one_isochrone(G, lat: float, lon: float, max_dist_m: float) -> BaseGeometry | None:
    """Concave-hull polygon of all OSM nodes within `max_dist_m` of (lat,lon)."""
    try:
        center = ox.nearest_nodes(G, X=lon, Y=lat)
    except Exception as e:
        print(f"  ! nearest_nodes failed at ({lat:.4f},{lon:.4f}): {e}", file=sys.stderr)
        return None
    subgraph = nx.ego_graph(G, center, radius=max_dist_m, distance="length")
    coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in subgraph.nodes]
    if len(coords) < 3:
        return None
    points = MultiPoint(coords)
    hull = shapely.concave_hull(points, ratio=CONCAVE_RATIO)
    if hull.is_empty or hull.geom_type not in ("Polygon", "MultiPolygon"):
        # Fall back to convex hull if concave fails (rare)
        hull = points.convex_hull
    return buffer_polygon_ft(hull, HULL_BUFFER_FT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int)
    parser.add_argument(
        "--force-redownload",
        action="store_true",
        help="Ignore cached OSM graph and re-download.",
    )
    args = parser.parse_args()

    venues_path = district_dir(args.district) / "venues.geojson"
    if not venues_path.exists():
        print(f"venues.geojson not found: {venues_path}", file=sys.stderr)
        return 1

    venues = json.loads(venues_path.read_text())
    if not venues.get("features"):
        print("No venues in file.", file=sys.stderr)
        return 1

    lons = [f["geometry"]["coordinates"][0] for f in venues["features"]]
    lats = [f["geometry"]["coordinates"][1] for f in venues["features"]]
    # ~0.0145 deg per mile at this latitude
    pad = NETWORK_BUFFER_MILES * 0.0145
    north, south = max(lats) + pad, min(lats) - pad
    east, west = max(lons) + pad, min(lons) - pad

    if args.force_redownload:
        cached = cache_dir() / f"network-d{args.district}.graphml"
        if cached.exists():
            cached.unlink()

    G = load_or_download_network(north, south, east, west, args.district)

    # Shell definitions: each entry maps a shell key to (outer_full, inner_full) keys.
    # The shell = outer_full - inner_full = the "additional reach" of that band, and is
    # what the UI renders so consecutive catchments don't compound alpha visually.
    SHELL_DEFS = [
        ("walk_15_only", "walk_15", "walk_10"),
        ("bike_10_only", "bike_10", "walk_15"),
        ("bike_15_only", "bike_15", "bike_10"),
    ]

    print(f"Computing catchments for {len(venues['features'])} venues × 4 profiles + shells...")
    out_features = []
    for i, venue in enumerate(venues["features"], start=1):
        venue_id = venue["properties"]["osm_id"]
        name = venue["properties"]["name"]
        lon, lat = venue["geometry"]["coordinates"]
        in_district_venue = venue["properties"].get("in_district", True)

        # Phase 1 — the four full polygons (needed for demographics aggregation later)
        polys: dict[str, BaseGeometry] = {}
        for profile_key, mode, minutes, mpm in PROFILES:
            max_dist_m = mpm * minutes
            poly = compute_one_isochrone(G, lat, lon, max_dist_m)
            if poly is None or poly.is_empty:
                continue
            polys[profile_key] = poly
            out_features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(poly),
                "properties": {
                    "venue_id": venue_id,
                    "venue_name": name,
                    "profile": profile_key,
                    "feature_type": "full",
                    "mode": mode,
                    "minutes": minutes,
                    "in_district_venue": in_district_venue,
                },
            })

        # Phase 2 — innermost shell (walk_10) aliases the full polygon
        if "walk_10" in polys:
            out_features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(polys["walk_10"]),
                "properties": {
                    "venue_id": venue_id,
                    "venue_name": name,
                    "profile": "walk_10",
                    "feature_type": "shell",
                    "mode": "walk",
                    "minutes": 10,
                    "in_district_venue": in_district_venue,
                },
            })

        # Phase 3 — outer shells, each = outer_full - inner_full
        for shell_key, outer_key, inner_key in SHELL_DEFS:
            if outer_key not in polys or inner_key not in polys:
                continue
            shell = polys[outer_key].difference(polys[inner_key])
            if shell.is_empty:
                continue
            mode = "walk" if shell_key.startswith("walk") else "bike"
            minutes = int(outer_key.rsplit("_", 1)[1])
            out_features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(shell),
                "properties": {
                    "venue_id": venue_id,
                    "venue_name": name,
                    "profile": shell_key,
                    "feature_type": "shell",
                    "mode": mode,
                    "minutes": minutes,
                    "in_district_venue": in_district_venue,
                },
            })

        if i % 10 == 0 or i == len(venues["features"]):
            print(f"  {i}/{len(venues['features'])} venues done")

    out_path = district_dir(args.district) / "catchments.geojson"
    out_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": out_features,
    }))
    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes; {len(out_features)} features)")

    # Quick stats: median catchment area per profile
    from collections import defaultdict
    areas_by_profile = defaultdict(list)
    for f in out_features:
        g = shape_from_geom(f["geometry"])
        # Project to EPSG:2226 for area in sq ft, then convert to acres
        area_acres = (
            gpd.GeoSeries([g], crs="EPSG:4326")
            .to_crs(epsg=2226)
            .iloc[0]
            .area / 43560
        )
        areas_by_profile[f["properties"]["profile"]].append(area_acres)

    print("\nMedian catchment area by profile (acres):")
    for profile_key, _, _, _ in PROFILES:
        areas = areas_by_profile.get(profile_key, [])
        if not areas:
            continue
        med = sorted(areas)[len(areas) // 2]
        print(f"  {profile_key:8s}  {med:8,.0f} ac  (n={len(areas)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
