#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.32",
#     "shapely>=2.0",
#     "pyproj>=3.6",
# ]
# ///
"""Render a print-ready SVG poster of a council district.

Outputs a 36×48" SVG with:
  * The district boundary (red with a white casing) over a world-mask
    that dims everything outside the polygon.
  * All OSM highways color-coded and width-scaled by class
    (motorway/trunk/primary/secondary/tertiary/residential/...).
  * Street name labels for entries on the print-street-labels.json
    allowlist (output of score-streets-for-print.py) plus all
    major-class names, placed greedily with simple AABB collision.
  * Title block, subtitle, and footer with attribution + date.

All sizes are point-units (1pt = 1/72 inch); viewBox is 2592×3456pt.
The SVG is editable in Illustrator/Inkscape — every street is a path
and every label is a real <text> element.

Dependencies are declared inline via PEP 723; invoke with `uv run`:

    scripts/render-print-svg.py 6

Use --force-refresh to re-query Overpass even if the cache exists.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from html import escape as xml_escape
from pathlib import Path

import requests
from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, shape
from shapely.ops import transform as shapely_transform, unary_union

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

WGS84_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32610", always_xy=True).transform

# ----- Print dimensions (must match printConfig.ts) -----
POSTER_W_IN = 36
POSTER_H_IN = 48
POSTER_W_PT = POSTER_W_IN * 72  # 2592
POSTER_H_PT = POSTER_H_IN * 72  # 3456

HEADER_HEIGHT_PT = 220
FOOTER_HEIGHT_PT = 80
PAGE_PADDING_PT = 48

MAP_TOP = HEADER_HEIGHT_PT
MAP_BOTTOM = POSTER_H_PT - FOOTER_HEIGHT_PT
MAP_HEIGHT = MAP_BOTTOM - MAP_TOP
MAP_WIDTH = POSTER_W_PT

# Map fit padding (so the district doesn't touch the canvas edge)
MAP_FIT_PADDING_PT = 60

# ----- Typography -----
TITLE_PT = 72
SUBTITLE_PT = 26
FOOTER_PT = 12

LABEL_MAJOR_PT = 14
LABEL_MINOR_PT = 7
LABEL_NEIGHBORHOOD_PT = 20

# Colors (match PrintMap.tsx)
COLOR_TITLE = "#0f172a"
COLOR_SUBTITLE = "#525252"
COLOR_FOOTER = "#6b7280"
COLOR_RULE = "#d4d4d4"

COLOR_BOUNDARY = "#b91c1c"
COLOR_BOUNDARY_CASING = "#ffffff"
BOUNDARY_WIDTH = 5
BOUNDARY_CASING_WIDTH = 10

MASK_FILL = "#ffffff"
MASK_OPACITY = 0.65

# Road styles, indexed by OSM highway class. Widths are point-units.
# Streets are drawn in two passes: first all casings, then all road colors.
# Adding a casing to a class means a darker "outline" appears under the road.
ROAD_STYLES = {
    "motorway":         {"color": "#d97706", "width": 3.0, "casing_color": "#b45309", "casing_width": 4.0, "tier": 5},
    "motorway_link":    {"color": "#d97706", "width": 2.0, "casing_color": "#b45309", "casing_width": 2.6, "tier": 5},
    "trunk":            {"color": "#404040", "width": 2.5, "casing_color": "#1f2937", "casing_width": 3.2, "tier": 5},
    "trunk_link":       {"color": "#404040", "width": 1.8, "tier": 5},
    "primary":          {"color": "#404040", "width": 2.5, "casing_color": "#1f2937", "casing_width": 3.2, "tier": 4},
    "primary_link":     {"color": "#404040", "width": 1.8, "tier": 4},
    "secondary":        {"color": "#525252", "width": 2.0, "casing_color": "#262626", "casing_width": 2.7, "tier": 3},
    "secondary_link":   {"color": "#525252", "width": 1.5, "tier": 3},
    "tertiary":         {"color": "#525252", "width": 2.0, "casing_color": "#262626", "casing_width": 2.7, "tier": 3},
    "tertiary_link":    {"color": "#525252", "width": 1.5, "tier": 3},
    "residential":      {"color": "#737373", "width": 1.4, "casing_color": "#525252", "casing_width": 1.8, "tier": 2},
    "unclassified":     {"color": "#737373", "width": 1.4, "casing_color": "#525252", "casing_width": 1.8, "tier": 2},
    "living_street":    {"color": "#737373", "width": 1.2, "tier": 2},
    "service":          {"color": "#a3a3a3", "width": 0.7, "tier": 1},
    "track":            {"color": "#a3a3a3", "width": 0.5, "tier": 1},
    "path":             {"color": "#a3a3a3", "width": 0.3, "tier": 0},
    "footway":          {"color": "#a3a3a3", "width": 0.3, "tier": 0},
    "cycleway":         {"color": "#a3a3a3", "width": 0.4, "tier": 0},
    "pedestrian":       {"color": "#a3a3a3", "width": 0.5, "tier": 0},
}

# Major-class highway classes (always labeled in addition to allowlist).
MAJOR_CLASSES = {"motorway", "trunk", "primary", "secondary", "tertiary"}


# ====================== Overpass + caching ======================

def overpass_query(south, west, north, east) -> str:
    """All highway ways in the bbox, with geometries and tags."""
    return f"""
[out:json][timeout:300];
(
  way["highway"]({south},{west},{north},{east});
);
out geom tags;
""".strip()


def fetch_overpass(query: str, cache_path: Path, force: bool = False) -> dict:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists() and not force:
        print(f"[cache] reading {cache_path}", file=sys.stderr)
        return json.loads(cache_path.read_text())
    headers = {
        "User-Agent": "smart-growth-visualizer/0.1 print-map-svg (local research)",
        "Accept": "application/json",
    }
    print(f"[overpass] querying ({len(query)} bytes)…", file=sys.stderr)
    t0 = time.time()
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=400)
    resp.raise_for_status()
    payload = resp.json()
    dt = time.time() - t0
    print(f"[overpass] {len(payload.get('elements', []))} elements in {dt:.1f}s",
          file=sys.stderr)
    cache_path.write_text(json.dumps(payload))
    return payload


# ====================== Geometry / projection ======================

def load_district_polygon(path: Path):
    data = json.loads(path.read_text())
    return unary_union([shape(f["geometry"]) for f in data["features"]])


def make_utm_to_svg(district_utm):
    """Return (transform_fn, district_svg_polygon, scale_pt_per_m)."""
    minx, miny, maxx, maxy = district_utm.bounds
    bbox_w = maxx - minx
    bbox_h = maxy - miny

    avail_w = MAP_WIDTH - 2 * MAP_FIT_PADDING_PT
    avail_h = MAP_HEIGHT - 2 * MAP_FIT_PADDING_PT
    scale = min(avail_w / bbox_w, avail_h / bbox_h)  # SVG pt per UTM meter

    map_cx = MAP_WIDTH / 2
    map_cy = (MAP_TOP + MAP_BOTTOM) / 2
    bbox_cx = (minx + maxx) / 2
    bbox_cy = (miny + maxy) / 2

    def to_svg(x_m, y_m):
        sx = map_cx + (x_m - bbox_cx) * scale
        # SVG y axis points DOWN; UTM y points UP.
        sy = map_cy - (y_m - bbox_cy) * scale
        return (sx, sy)

    return to_svg, scale


def way_to_utm_line(way):
    geom = way.get("geometry")
    if not geom or len(geom) < 2:
        return None
    wgs = LineString([(p["lon"], p["lat"]) for p in geom])
    return shapely_transform(WGS84_TO_UTM, wgs)


# ====================== SVG path helpers ======================

def path_d_from_line(line, to_svg) -> str:
    """LineString → SVG path 'd' string, no rounding loss."""
    coords = list(line.coords)
    pts = [to_svg(x, y) for x, y in coords]
    parts = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for x, y in pts[1:]:
        parts.append(f"L{x:.1f},{y:.1f}")
    return "".join(parts)


def world_mask_path_d(district_utm, to_svg) -> str:
    """SVG path: map area rectangle with district polygon punched out."""
    # Outer rectangle: the entire map band
    outer = [
        (0, MAP_TOP),
        (POSTER_W_PT, MAP_TOP),
        (POSTER_W_PT, MAP_BOTTOM),
        (0, MAP_BOTTOM),
    ]
    parts = [f"M{outer[0][0]:.1f},{outer[0][1]:.1f}"]
    for x, y in outer[1:]:
        parts.append(f"L{x:.1f},{y:.1f}")
    parts.append("Z")

    rings = []
    if district_utm.geom_type == "Polygon":
        rings.append(list(district_utm.exterior.coords))
    else:
        for poly in district_utm.geoms:
            rings.append(list(poly.exterior.coords))

    for ring in rings:
        svg_pts = [to_svg(x, y) for x, y in ring]
        parts.append(f"M{svg_pts[0][0]:.1f},{svg_pts[0][1]:.1f}")
        for x, y in svg_pts[1:]:
            parts.append(f"L{x:.1f},{y:.1f}")
        parts.append("Z")

    return "".join(parts)


# ====================== Label placement ======================

def estimate_text_width_pt(text: str, size_pt: float) -> float:
    """Rough sans-serif text width. 0.55em per character is a decent average."""
    return len(text) * size_pt * 0.55


def rect_overlap(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def pick_label_anchor(svg_lines, label_w, label_h):
    """Return (cx, cy) and the anchored bounding box for the longest segment.

    We use the midpoint of the line whose on-poster length is longest, so the
    label sits where the street is most visible.
    """
    best = None
    best_len = -1.0
    for svg_line in svg_lines:
        if len(svg_line) < 2:
            continue
        # Compute total length and walk to midpoint
        seg_lens = []
        total = 0.0
        for i in range(1, len(svg_line)):
            dx = svg_line[i][0] - svg_line[i - 1][0]
            dy = svg_line[i][1] - svg_line[i - 1][1]
            d = (dx * dx + dy * dy) ** 0.5
            seg_lens.append(d)
            total += d
        if total <= 0:
            continue
        if total > best_len:
            best_len = total
            # Walk to midpoint
            half = total / 2
            acc = 0.0
            mid = svg_line[0]
            for i, d in enumerate(seg_lens):
                if acc + d >= half:
                    t = (half - acc) / d if d > 0 else 0
                    x0, y0 = svg_line[i]
                    x1, y1 = svg_line[i + 1]
                    mid = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
                    break
                acc += d
            best = (mid, total)
    if best is None:
        return None, None
    (cx, cy), street_len = best
    # Require the street to be at least as long as the label, otherwise skip.
    if street_len < label_w * 0.9:
        return None, None
    bbox = (cx - label_w / 2, cy - label_h / 2, cx + label_w / 2, cy + label_h / 2)
    return (cx, cy), bbox


def place_labels(streets_for_label, to_svg):
    """Greedy AABB-collision label placement, highest priority first."""
    placed = []
    for s in sorted(streets_for_label, key=lambda r: -r["priority"]):
        size = s["size_pt"]
        text = s["name"]
        label_w = estimate_text_width_pt(text, size)
        label_h = size * 1.2
        # Convert each utm line of this street to SVG pixel points
        svg_lines = []
        for utm_line in s["lines"]:
            pts = [to_svg(x, y) for x, y in utm_line.coords]
            svg_lines.append(pts)
        anchor, bbox = pick_label_anchor(svg_lines, label_w, label_h)
        if bbox is None:
            continue
        if any(rect_overlap(bbox, b) for (b, _) in placed):
            continue
        placed.append((bbox, {
            "x": anchor[0],
            "y": anchor[1],
            "size": size,
            "text": text,
            "color": s["color"],
            "halo": s["halo"],
            "halo_width": s["halo_width"],
        }))
    return [p[1] for p in placed]


# ====================== Aggregation ======================

def aggregate_ways(payload, district_utm):
    """Return: list of dicts, one per OSM way clipped to UTM, plus per-name index."""
    ways = []  # all clipped ways with style info
    by_name = {}  # name → {lines: [LineString], classes: set}
    for el in payload.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags") or {}
        highway = tags.get("highway")
        if not highway:
            continue
        style = ROAD_STYLES.get(highway)
        if style is None:
            continue  # unknown class; skip
        utm = way_to_utm_line(el)
        if utm is None:
            continue
        clipped = utm.intersection(district_utm.buffer(800))  # small buffer for context
        if clipped.is_empty:
            continue
        # Normalise to LineString iterable
        lines = []
        if clipped.geom_type == "LineString":
            lines.append(clipped)
        elif clipped.geom_type == "MultiLineString":
            for ls in clipped.geoms:
                lines.append(ls)
        else:
            continue
        for ls in lines:
            ways.append({"line": ls, "class": highway, "style": style})
            name = tags.get("name")
            if name:
                bucket = by_name.setdefault(
                    name, {"lines": [], "classes": set()}
                )
                bucket["lines"].append(ls)
                bucket["classes"].add(highway)
    return ways, by_name


# ====================== SVG assembly ======================

def render_svg(district_n, district_utm, ways, by_name, allowlist) -> str:
    to_svg, scale = make_utm_to_svg(district_utm)

    out = []
    out.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{POSTER_W_IN}in" height="{POSTER_H_IN}in" '
        f'viewBox="0 0 {POSTER_W_PT} {POSTER_H_PT}" '
        f'font-family="Helvetica,Arial,sans-serif">'
    )
    # Background
    out.append(f'<rect width="{POSTER_W_PT}" height="{POSTER_H_PT}" fill="#ffffff"/>')

    # ---- Streets: casings first, then road colors. Both sorted by tier so
    # higher-class roads paint over lower-class ones.
    out.append('<g id="streets">')
    # Pass 1: casings
    out.append('<g id="casings">')
    for w in sorted(ways, key=lambda x: x["style"].get("tier", 0)):
        st = w["style"]
        if "casing_color" not in st:
            continue
        d = path_d_from_line(w["line"], to_svg)
        out.append(
            f'<path d="{d}" stroke="{st["casing_color"]}" '
            f'stroke-width="{st["casing_width"]}" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )
    out.append('</g>')
    # Pass 2: road fills
    out.append('<g id="roads">')
    for w in sorted(ways, key=lambda x: x["style"].get("tier", 0)):
        st = w["style"]
        d = path_d_from_line(w["line"], to_svg)
        out.append(
            f'<path d="{d}" stroke="{st["color"]}" '
            f'stroke-width="{st["width"]}" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )
    out.append('</g>')
    out.append('</g>')

    # ---- World mask: dim everything outside the district.
    mask_d = world_mask_path_d(district_utm, to_svg)
    out.append(
        f'<path id="world-mask" d="{mask_d}" fill="{MASK_FILL}" '
        f'fill-opacity="{MASK_OPACITY}" fill-rule="evenodd"/>'
    )

    # ---- District boundary: casing then line.
    boundary_paths = []
    if district_utm.geom_type == "Polygon":
        rings = [list(district_utm.exterior.coords)]
    else:
        rings = [list(p.exterior.coords) for p in district_utm.geoms]
    for ring in rings:
        svg_pts = [to_svg(x, y) for x, y in ring]
        parts = [f"M{svg_pts[0][0]:.1f},{svg_pts[0][1]:.1f}"]
        for x, y in svg_pts[1:]:
            parts.append(f"L{x:.1f},{y:.1f}")
        parts.append("Z")
        boundary_paths.append("".join(parts))
    boundary_d = " ".join(boundary_paths)
    out.append(
        f'<path id="boundary-casing" d="{boundary_d}" '
        f'stroke="{COLOR_BOUNDARY_CASING}" stroke-width="{BOUNDARY_CASING_WIDTH}" '
        f'fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    out.append(
        f'<path id="boundary-line" d="{boundary_d}" '
        f'stroke="{COLOR_BOUNDARY}" stroke-width="{BOUNDARY_WIDTH}" '
        f'fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # ---- Labels: build list of (name, lines, size, priority).
    label_set = set(allowlist) | {
        name for name, b in by_name.items() if b["classes"] & MAJOR_CLASSES
    }
    streets_for_label = []
    for name in label_set:
        bucket = by_name.get(name)
        if bucket is None:
            continue
        is_major = bool(bucket["classes"] & MAJOR_CLASSES)
        streets_for_label.append({
            "name": name,
            "lines": bucket["lines"],
            "size_pt": LABEL_MAJOR_PT if is_major else LABEL_MINOR_PT,
            "color": "#1f2937" if is_major else "#374151",
            "halo": "#ffffff",
            "halo_width": 1.5 if is_major else 1.0,
            "priority": (10 if is_major else 0)
            + sum(ls.length for ls in bucket["lines"]) / 100.0,
        })

    labels = place_labels(streets_for_label, to_svg)
    out.append('<g id="labels">')
    for lbl in labels:
        # paint-order=stroke draws the halo (stroke) underneath the fill,
        # producing the classic cartographic halo.
        out.append(
            f'<text x="{lbl["x"]:.1f}" y="{lbl["y"]:.1f}" '
            f'font-size="{lbl["size"]}" font-weight="500" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'fill="{lbl["color"]}" stroke="{lbl["halo"]}" '
            f'stroke-width="{lbl["halo_width"]}" '
            f'paint-order="stroke" stroke-linejoin="round">'
            f'{xml_escape(lbl["text"])}</text>'
        )
    out.append('</g>')

    # ---- Header
    rule_y = HEADER_HEIGHT_PT
    out.append(
        f'<g id="header">'
        f'<text x="{PAGE_PADDING_PT}" y="{HEADER_HEIGHT_PT - 80}" '
        f'font-size="{TITLE_PT}" font-weight="600" fill="{COLOR_TITLE}" '
        f'dominant-baseline="text-after-edge">Chico City Council District {district_n}</text>'
        f'<text x="{PAGE_PADDING_PT}" y="{HEADER_HEIGHT_PT - 30}" '
        f'font-size="{SUBTITLE_PT}" fill="{COLOR_SUBTITLE}">Streets &amp; District Boundary</text>'
        f'<line x1="0" y1="{rule_y}" x2="{POSTER_W_PT}" y2="{rule_y}" '
        f'stroke="{COLOR_RULE}" stroke-width="0.75"/>'
        f'</g>'
    )

    # ---- Footer
    foot_y = MAP_BOTTOM
    date_str = datetime.now(timezone.utc).date().isoformat()
    out.append(
        f'<g id="footer">'
        f'<line x1="0" y1="{foot_y}" x2="{POSTER_W_PT}" y2="{foot_y}" '
        f'stroke="{COLOR_RULE}" stroke-width="0.75"/>'
        f'<text x="{PAGE_PADDING_PT}" y="{foot_y + FOOTER_HEIGHT_PT / 2}" '
        f'font-size="{FOOTER_PT}" fill="{COLOR_FOOTER}" '
        f'dominant-baseline="middle">Data: OpenStreetMap contributors · City of Chico</text>'
        f'<text x="{POSTER_W_PT - PAGE_PADDING_PT}" y="{foot_y + FOOTER_HEIGHT_PT / 2}" '
        f'font-size="{FOOTER_PT}" fill="{COLOR_FOOTER}" '
        f'text-anchor="end" dominant-baseline="middle">Generated {date_str}</text>'
        f'</g>'
    )

    out.append('</svg>')
    return "\n".join(out)


# ====================== Main ======================

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("district", type=int, help="Council district number (e.g. 6)")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument(
        "--out",
        type=Path,
        help="Output SVG path (default: public/data/candidate-district-N/print-map.svg)",
    )
    args = parser.parse_args()

    base = PROJECT_ROOT / "public" / "data" / f"candidate-district-{args.district}"
    boundary_path = base / "district-boundary.geojson"
    labels_path = base / "print-street-labels.json"
    out_path = args.out or (base / "print-map.svg")
    cache_path = PROJECT_ROOT / ".cache" / "overpass" / f"district-{args.district}-all-highways.json"

    if not boundary_path.exists():
        sys.exit(f"Boundary file not found: {boundary_path}")
    if not labels_path.exists():
        sys.exit(
            f"Allowlist not found: {labels_path}\n"
            f"Run scripts/score-streets-for-print.py first."
        )

    print(f"[district {args.district}] loading boundary…", file=sys.stderr)
    district_wgs = load_district_polygon(boundary_path)
    district_utm = shapely_transform(WGS84_TO_UTM, district_wgs)

    miny, minx, maxy, maxx = (
        district_wgs.bounds[1],
        district_wgs.bounds[0],
        district_wgs.bounds[3],
        district_wgs.bounds[2],
    )
    query = overpass_query(miny, minx, maxy, maxx)
    payload = fetch_overpass(query, cache_path, force=args.force_refresh)

    print(f"[district {args.district}] aggregating ways…", file=sys.stderr)
    ways, by_name = aggregate_ways(payload, district_utm)
    print(
        f"[district {args.district}] {len(ways)} way segments, "
        f"{len(by_name)} unique street names",
        file=sys.stderr,
    )

    labels_data = json.loads(labels_path.read_text())
    allowlist = labels_data.get("allowlist", [])

    svg = render_svg(args.district, district_utm, ways, by_name, allowlist)
    out_path.write_text(svg)

    size_kb = out_path.stat().st_size / 1024
    label_count = svg.count("<text")
    print(
        f"[out] wrote {out_path}\n"
        f"      {size_kb:,.0f} KB  ({size_kb / 1024:.1f} MB)\n"
        f"      {label_count} <text> elements (streets + chrome)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
