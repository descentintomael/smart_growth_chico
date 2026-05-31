#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.32",
#     "shapely>=2.0",
#     "pyproj>=3.6",
# ]
# ///
"""Score named streets in a council district for print-poster labeling.

For each named highway segment from OpenStreetMap inside the district polygon,
we sum its in-district length, count any OSM `addr:street` matches, and add a
class bonus (residential/tertiary/secondary/primary). The resulting per-name
score lets us decide which streets are worth labeling on the print poster vs
which are clutter.

Output JSON shape:
    {
      "generated": "<ISO date>",
      "district": 6,
      "queried_at": "<ISO datetime>",
      "all_named_streets": [
          { "name": "...", "score": X, "length_m": ..., "addr_count": ...,
            "classes": ["residential"] },
          ...
      ],
      "summary": {
          "total_named_streets": N,
          "score_percentiles": { "p10": .., "p25": .., "p50": .., "p75": .., "p90": .. }
      }
    }

Caching:
    Overpass responses are cached under .cache/overpass/<district>-streets.json
    keyed on the district bbox. Delete the file to force a re-query.

Usage:
    scripts/score-streets-for-print.py 6
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from pyproj import Transformer
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform, unary_union

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# UTM zone 10N — Northern California. Use this for accurate meter lengths.
WGS84_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32610", always_xy=True).transform

# Highway classes worth considering for "named street" coverage. Service and
# track are typically driveways / fire roads — we'll drop them via class filter.
ELIGIBLE_HIGHWAY_CLASSES = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "living_street",
    "motorway_link",
    "trunk_link",
    "primary_link",
    "secondary_link",
    "tertiary_link",
}

# Class bonus added to the score. Higher class = more navigationally important.
CLASS_BONUS = {
    "motorway": 20,
    "trunk": 18,
    "primary": 15,
    "secondary": 10,
    "tertiary": 6,
    "unclassified": 2,
    "residential": 0,
    "living_street": 0,
    "motorway_link": 5,
    "trunk_link": 5,
    "primary_link": 4,
    "secondary_link": 3,
    "tertiary_link": 2,
}


def district_paths(district: int) -> tuple[Path, Path, Path]:
    """Return (boundary_geojson, output_json, cache_json) paths."""
    base = PROJECT_ROOT / "public" / "data" / f"candidate-district-{district}"
    boundary = base / "district-boundary.geojson"
    output = base / "print-street-labels.json"
    cache = PROJECT_ROOT / ".cache" / "overpass" / f"district-{district}-streets.json"
    return boundary, output, cache


def load_district_polygon(boundary_path: Path):
    """Return a shapely (multi)polygon for the district."""
    data = json.loads(boundary_path.read_text())
    geoms = [shape(f["geometry"]) for f in data["features"]]
    return unary_union(geoms)


def bbox_of(geom) -> tuple[float, float, float, float]:
    """(south, west, north, east) — Overpass bbox order."""
    minx, miny, maxx, maxy = geom.bounds
    return (miny, minx, maxy, maxx)


def overpass_query(south, west, north, east) -> str:
    return f"""
[out:json][timeout:240];
(
  way["highway"]["name"]({south},{west},{north},{east});
  way["addr:street"]({south},{west},{north},{east});
  node["addr:street"]({south},{west},{north},{east});
);
out geom tags;
""".strip()


def fetch_overpass(query: str, cache_path: Path, force: bool = False) -> dict:
    """Run Overpass query, caching the JSON response."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not force:
        print(f"[cache] reading {cache_path}", file=sys.stderr)
        return json.loads(cache_path.read_text())

    print(f"[overpass] querying ({len(query)} bytes)…", file=sys.stderr)
    headers = {
        "User-Agent": "smart-growth-visualizer/0.1 print-map-research (local research)",
        "Accept": "application/json",
    }
    t0 = time.time()
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=300)
    resp.raise_for_status()
    payload = resp.json()
    dt = time.time() - t0
    print(
        f"[overpass] {len(payload.get('elements', []))} elements in {dt:.1f}s",
        file=sys.stderr,
    )
    cache_path.write_text(json.dumps(payload, indent=2))
    return payload


def way_to_linestring(way: dict) -> LineString | None:
    geom = way.get("geometry")
    if not geom or len(geom) < 2:
        return None
    return LineString([(p["lon"], p["lat"]) for p in geom])


def in_district_length_m(line: LineString, district_polygon) -> float:
    """Length of the in-district portion of a way, in meters."""
    clipped = line.intersection(district_polygon)
    if clipped.is_empty:
        return 0.0
    projected = transform(WGS84_TO_UTM, clipped)
    return float(projected.length)


def score_streets(payload: dict, district_polygon) -> list[dict]:
    """Aggregate per-street-name stats and compute scores."""
    by_name: dict[str, dict] = {}

    # Pass 1: named highways → length, classes
    for el in payload.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags") or {}
        name = tags.get("name")
        highway = tags.get("highway")
        if not name or not highway:
            continue
        if highway not in ELIGIBLE_HIGHWAY_CLASSES:
            continue
        line = way_to_linestring(el)
        if line is None:
            continue
        length_m = in_district_length_m(line, district_polygon)
        if length_m <= 0:
            continue
        bucket = by_name.setdefault(
            name,
            {"name": name, "length_m": 0.0, "addr_count": 0, "classes": set()},
        )
        bucket["length_m"] += length_m
        bucket["classes"].add(highway)

    # Pass 2: addr:street counts within district
    for el in payload.get("elements", []):
        tags = el.get("tags") or {}
        street = tags.get("addr:street")
        if not street:
            continue
        # Need a point or representative geometry inside district
        if el.get("type") == "node":
            pt = Point(el["lon"], el["lat"])
        elif el.get("type") == "way":
            line = way_to_linestring(el)
            if line is None:
                continue
            pt = line.representative_point()
        else:
            continue
        if not district_polygon.contains(pt):
            continue
        if street not in by_name:
            # The street name is referenced by an address but didn't show up as
            # a named way inside the district. Still useful to count it; init.
            by_name[street] = {
                "name": street,
                "length_m": 0.0,
                "addr_count": 0,
                "classes": set(),
            }
        by_name[street]["addr_count"] += 1

    # Compute scores
    out = []
    for name, b in by_name.items():
        classes = sorted(b["classes"])
        class_bonus = max((CLASS_BONUS.get(c, 0) for c in classes), default=0)
        length_score = b["length_m"] / 100.0  # 1 point per 100m of in-district street
        addr_score = b["addr_count"] * 0.5  # half a point per OSM address
        score = round(length_score + addr_score + class_bonus, 2)
        out.append(
            {
                "name": name,
                "score": score,
                "length_m": round(b["length_m"], 1),
                "addr_count": b["addr_count"],
                "classes": classes,
                "class_bonus": class_bonus,
            }
        )
    out.sort(key=lambda r: (-r["score"], r["name"]))
    return out


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return round(s[f] + (s[c] - s[f]) * (k - f), 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="Council district number (e.g. 6)")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Re-query Overpass even if a cached response exists",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Minimum score for the allowlist (default: 3.0, ≈ top 45%% of named streets)",
    )
    args = parser.parse_args()

    boundary_path, output_path, cache_path = district_paths(args.district)
    if not boundary_path.exists():
        sys.exit(f"Boundary file not found: {boundary_path}")

    district_polygon = load_district_polygon(boundary_path)
    bbox = bbox_of(district_polygon)
    print(
        f"[district {args.district}] bbox south,west,north,east = "
        f"({bbox[0]:.5f}, {bbox[1]:.5f}, {bbox[2]:.5f}, {bbox[3]:.5f})",
        file=sys.stderr,
    )

    query = overpass_query(*bbox)
    payload = fetch_overpass(query, cache_path, force=args.force_refresh)

    rows = score_streets(payload, district_polygon)
    scores = [r["score"] for r in rows]
    summary = {
        "total_named_streets": len(rows),
        "score_percentiles": {
            "p10": percentile(scores, 10),
            "p25": percentile(scores, 25),
            "p50": percentile(scores, 50),
            "p75": percentile(scores, 75),
            "p90": percentile(scores, 90),
            "p95": percentile(scores, 95),
        },
    }

    allowlist = sorted({r["name"] for r in rows if r["score"] >= args.threshold})
    summary["threshold"] = args.threshold
    summary["allowlist_size"] = len(allowlist)
    summary["coverage_pct"] = round(100 * len(allowlist) / max(len(rows), 1), 1)

    out = {
        "generated": datetime.now(timezone.utc).date().isoformat(),
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "district": args.district,
        "summary": summary,
        "allowlist": allowlist,
        "all_named_streets": rows,
    }
    output_path.write_text(json.dumps(out, indent=2))
    print(
        f"[out] wrote {output_path} ({len(rows)} streets, "
        f"allowlist={len(allowlist)} @ threshold={args.threshold}, "
        f"{output_path.stat().st_size:,} bytes)",
        file=sys.stderr,
    )

    # Surface top streets so we can sanity-check at the terminal.
    print("\nTop 20 streets by score:", file=sys.stderr)
    for r in rows[:20]:
        cls = ",".join(r["classes"]) or "—"
        print(
            f"  {r['score']:7.2f}  len={r['length_m']:7.1f}m  "
            f"addr={r['addr_count']:3d}  [{cls}]  {r['name']}",
            file=sys.stderr,
        )
    print(f"\nPercentiles: {summary['score_percentiles']}", file=sys.stderr)


if __name__ == "__main__":
    main()
