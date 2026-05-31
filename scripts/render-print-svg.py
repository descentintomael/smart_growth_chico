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
  * Landuse / leisure / water polygons (parks, schools, lakes, etc.)
    rendered in subtle, professional pastel tints under the road network.
  * Waterways (creeks, streams) drawn as blue lines.
  * All OSM highways color-coded and width-scaled by class
    (motorway/trunk/primary/secondary/tertiary/residential/...).
  * A thin red district-boundary line over a world-mask that dims
    everything outside the polygon.
  * Street name labels — including residential streets from the
    print-street-labels.json allowlist plus all major-class names —
    placed via SVG <textPath> so each label curves along its road.
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
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Polygon,
    shape,
)
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

# Header / footer
COLOR_TITLE = "#0f172a"
COLOR_SUBTITLE = "#525252"
COLOR_FOOTER = "#6b7280"
COLOR_RULE = "#d4d4d4"

# Paper background — slightly warm off-white so the poster feels printed,
# not screen-bright. Subtle enough that pastels still pop.
COLOR_BG = "#fbfaf6"

# District boundary — single thin red line, no casing. The mask handles the
# in/out separation; this is just an indicator, not the dominant visual.
COLOR_BOUNDARY = "#b91c1c"
BOUNDARY_WIDTH = 1.5

# World mask — dims everything outside the district polygon.
MASK_FILL = "#ffffff"
MASK_OPACITY = 0.55

# Road styles, indexed by OSM highway class. Two-pass render: casings first
# (drawn for arterials only), then road fills on top.
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

MAJOR_CLASSES = {"motorway", "trunk", "primary", "secondary", "tertiary"}

# Landuse / zone styles — pale, professional pastels. Each entry maps the
# classification key (assigned by `classify_landuse`) to a fill color.
# z-order matters: lower-tier zones get painted first, so things like
# sports fields paint over the underlying park.
LANDUSE_STYLES = {
    # tier, fill
    "forest":     {"fill": "#cfdcc0", "tier": 1},
    "wood":       {"fill": "#cfdcc0", "tier": 1},
    "grass":      {"fill": "#e6efd0", "tier": 1},
    "farmland":   {"fill": "#eee9d2", "tier": 1},
    "meadow":     {"fill": "#e6eecf", "tier": 1},
    "cemetery":   {"fill": "#dadfca", "tier": 2},
    "park":       {"fill": "#d6e4c4", "tier": 2},
    "sports":     {"fill": "#c8dfb8", "tier": 3},
    "playground": {"fill": "#d4e6c2", "tier": 3},
    "school":     {"fill": "#fbe6b0", "tier": 4},
    "hospital":   {"fill": "#eecaca", "tier": 4},
    "industrial": {"fill": "#dedede", "tier": 2},
    "commercial": {"fill": "#e7e4ea", "tier": 2},
    "retail":     {"fill": "#ebd9c8", "tier": 2},
    "water":      {"fill": "#bfd6e8", "tier": 6},  # always on top of land
}

WATERWAY_STYLES = {
    "river":  {"color": "#7fa5c4", "width": 1.6},
    "stream": {"color": "#7fa5c4", "width": 0.7},
    "canal":  {"color": "#7fa5c4", "width": 1.0},
}


def classify_landuse(tags: dict) -> str | None:
    """Map OSM tags → a single landuse class. Returns None if not interesting."""
    water = tags.get("water")
    natural = tags.get("natural")
    landuse = tags.get("landuse")
    leisure = tags.get("leisure")
    amenity = tags.get("amenity")

    if water or natural == "water":
        return "water"
    if natural == "wood" or landuse == "forest":
        return "forest"
    if landuse == "cemetery":
        return "cemetery"
    if leisure in ("park", "garden", "nature_reserve"):
        return "park"
    if landuse in ("park", "recreation_ground"):
        return "park"
    if landuse in ("grass", "meadow"):
        return "grass"
    if landuse == "farmland":
        return "farmland"
    if leisure in ("stadium", "sports_centre", "pitch"):
        return "sports"
    if leisure == "playground":
        return "playground"
    if amenity in ("school", "university", "college", "kindergarten"):
        return "school"
    if amenity == "hospital":
        return "hospital"
    if landuse == "industrial":
        return "industrial"
    if landuse == "commercial":
        return "commercial"
    if landuse == "retail":
        return "retail"
    return None


# ====================== Overpass + caching ======================

def overpass_query(south, west, north, east) -> str:
    """All highways + landuse/leisure/water/amenity features in the bbox."""
    return f"""
[out:json][timeout:400];
(
  way["highway"]({south},{west},{north},{east});
  way["landuse"~"^(park|recreation_ground|grass|forest|cemetery|industrial|commercial|retail|meadow|farmland)$"]({south},{west},{north},{east});
  way["leisure"~"^(park|garden|playground|stadium|sports_centre|pitch|nature_reserve)$"]({south},{west},{north},{east});
  way["natural"~"^(water|wood)$"]({south},{west},{north},{east});
  way["water"]({south},{west},{north},{east});
  way["amenity"~"^(school|university|college|hospital|kindergarten)$"]({south},{west},{north},{east});
  way["waterway"~"^(river|stream|canal)$"]({south},{west},{north},{east});
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
    minx, miny, maxx, maxy = district_utm.bounds
    bbox_w = maxx - minx
    bbox_h = maxy - miny

    avail_w = MAP_WIDTH - 2 * MAP_FIT_PADDING_PT
    avail_h = MAP_HEIGHT - 2 * MAP_FIT_PADDING_PT
    scale = min(avail_w / bbox_w, avail_h / bbox_h)

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


def way_to_utm_polygon(way):
    """Way geometry → shapely Polygon (closed). Returns None if not closeable."""
    geom = way.get("geometry")
    if not geom or len(geom) < 3:
        return None
    coords = [(p["lon"], p["lat"]) for p in geom]
    # Some OSM ways tagged as areas aren't explicitly closed.
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            return None
        return shapely_transform(WGS84_TO_UTM, poly)
    except Exception:
        return None


# ====================== SVG path helpers ======================

def path_d_from_line(line, to_svg) -> str:
    coords = list(line.coords)
    pts = [to_svg(x, y) for x, y in coords]
    parts = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for x, y in pts[1:]:
        parts.append(f"L{x:.1f},{y:.1f}")
    return "".join(parts)


def path_d_from_svg_coords(coords) -> str:
    parts = [f"M{coords[0][0]:.1f},{coords[0][1]:.1f}"]
    for x, y in coords[1:]:
        parts.append(f"L{x:.1f},{y:.1f}")
    return "".join(parts)


def path_d_from_polygon(poly, to_svg) -> str:
    """Polygon (with optional holes) → SVG path d. Use fill-rule='evenodd'."""
    parts = []
    rings = [list(poly.exterior.coords)] + [list(h.coords) for h in poly.interiors]
    for ring in rings:
        svg_pts = [to_svg(x, y) for x, y in ring]
        parts.append(f"M{svg_pts[0][0]:.1f},{svg_pts[0][1]:.1f}")
        for x, y in svg_pts[1:]:
            parts.append(f"L{x:.1f},{y:.1f}")
        parts.append("Z")
    return "".join(parts)


def world_mask_path_d(district_utm, to_svg) -> str:
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
    return len(text) * size_pt * 0.55


def rect_overlap(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def label_anchor_and_bbox(svg_coords, label_w, label_h):
    """Return (midpoint, bbox) for a label centered on the longest in-line segment.

    Returns (None, None) if the line is too short to host the label.
    """
    if len(svg_coords) < 2:
        return None, None
    # Total length and per-segment lengths
    seg_lens = []
    total = 0.0
    for i in range(1, len(svg_coords)):
        dx = svg_coords[i][0] - svg_coords[i - 1][0]
        dy = svg_coords[i][1] - svg_coords[i - 1][1]
        d = (dx * dx + dy * dy) ** 0.5
        seg_lens.append(d)
        total += d
    if total < label_w * 0.9:
        return None, None
    half = total / 2
    acc = 0.0
    mid = svg_coords[0]
    for i, d in enumerate(seg_lens):
        if acc + d >= half:
            t = (half - acc) / d if d > 0 else 0
            x0, y0 = svg_coords[i]
            x1, y1 = svg_coords[i + 1]
            mid = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            break
        acc += d
    bbox = (mid[0] - label_w / 2, mid[1] - label_h / 2,
            mid[0] + label_w / 2, mid[1] + label_h / 2)
    return mid, bbox


def reorient_for_readability(svg_coords):
    """Reverse the path if it would render text upside-down or bottom-up.

    For mostly-horizontal paths we want net dx > 0 (left-to-right).
    For mostly-vertical paths we want net dy > 0 (top-to-bottom in SVG).
    """
    if len(svg_coords) < 2:
        return svg_coords
    sx, sy = svg_coords[0]
    ex, ey = svg_coords[-1]
    dx = ex - sx
    dy = ey - sy
    if abs(dy) > abs(dx):
        if dy < 0:
            return list(reversed(svg_coords))
    else:
        if dx < 0:
            return list(reversed(svg_coords))
    return svg_coords


def place_labels(streets_for_label, to_svg):
    """Greedy AABB-collision label placement, highest priority first.

    Returns a list of dicts: { def_path_d, def_id, size, text, color, halo,
    halo_width }. The textPath then references def_id.
    """
    placed = []
    out = []
    idx = 0
    for s in sorted(streets_for_label, key=lambda r: -r["priority"]):
        size = s["size_pt"]
        text = s["name"]
        label_w = estimate_text_width_pt(text, size)
        label_h = size * 1.2

        # Pick the longest line as the label baseline
        longest = max(s["lines"], key=lambda l: l.length)
        svg_coords = [to_svg(x, y) for x, y in longest.coords]
        anchor, bbox = label_anchor_and_bbox(svg_coords, label_w, label_h)
        if bbox is None:
            continue
        if any(rect_overlap(bbox, b) for (b, _) in placed):
            continue

        # Make sure the path is right-side-up for the chosen baseline.
        oriented = reorient_for_readability(svg_coords)
        path_d = path_d_from_svg_coords(oriented)

        idx += 1
        def_id = f"lp-{idx}"
        out.append({
            "def_id": def_id,
            "def_path_d": path_d,
            "size": size,
            "text": text,
            "color": s["color"],
            "halo": s["halo"],
            "halo_width": s["halo_width"],
            "weight": s.get("weight", 500),
        })
        placed.append((bbox, def_id))
    return out


# ====================== Aggregation ======================

def aggregate_features(payload, district_utm):
    """Return (highway_ways, landuse_polygons, waterway_lines, named_lines_by_name).

    Everything is clipped to a small buffer around the district polygon so the
    rendered map keeps a bit of context around the boundary.
    """
    context = district_utm.buffer(800)  # ~800m context margin

    highway_ways = []
    landuse_polys = []  # list of (polygon, class_key)
    waterway_lines = []  # list of (line, waterway_kind)
    by_name = {}

    for el in payload.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags") or {}

        # ---- Waterways ----
        waterway = tags.get("waterway")
        if waterway in WATERWAY_STYLES:
            utm = way_to_utm_line(el)
            if utm is None:
                continue
            clipped = utm.intersection(context)
            if clipped.is_empty:
                continue
            if clipped.geom_type == "LineString":
                waterway_lines.append((clipped, waterway))
            elif clipped.geom_type == "MultiLineString":
                for sub in clipped.geoms:
                    waterway_lines.append((sub, waterway))
            continue  # waterway tag exclusive

        # ---- Landuse / zones ----
        cls = classify_landuse(tags)
        if cls is not None and cls in LANDUSE_STYLES:
            poly_utm = way_to_utm_polygon(el)
            if poly_utm is None:
                continue
            clipped = poly_utm.intersection(context)
            if clipped.is_empty:
                continue
            if clipped.geom_type == "Polygon":
                landuse_polys.append((clipped, cls))
            elif clipped.geom_type == "MultiPolygon":
                for sub in clipped.geoms:
                    landuse_polys.append((sub, cls))
            # NB: do NOT continue here — a school might also have addr tags etc.;
            # but landuse + highway aren't mixed, so we can skip the rest if no
            # highway tag.
            if not tags.get("highway"):
                continue

        # ---- Highways ----
        highway = tags.get("highway")
        if highway is None:
            continue
        style = ROAD_STYLES.get(highway)
        if style is None:
            continue
        utm = way_to_utm_line(el)
        if utm is None:
            continue
        clipped = utm.intersection(context)
        if clipped.is_empty:
            continue
        lines = []
        if clipped.geom_type == "LineString":
            lines.append(clipped)
        elif clipped.geom_type == "MultiLineString":
            lines.extend(clipped.geoms)
        else:
            continue
        for ls in lines:
            highway_ways.append({"line": ls, "class": highway, "style": style})
            name = tags.get("name")
            if name:
                bucket = by_name.setdefault(
                    name, {"lines": [], "classes": set()}
                )
                bucket["lines"].append(ls)
                bucket["classes"].add(highway)

    return highway_ways, landuse_polys, waterway_lines, by_name


# ====================== SVG assembly ======================

def render_svg(district_n, district_utm, highway_ways, landuse_polys, waterway_lines, by_name, allowlist):
    to_svg, _ = make_utm_to_svg(district_utm)

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{POSTER_W_IN}in" height="{POSTER_H_IN}in" '
        f'viewBox="0 0 {POSTER_W_PT} {POSTER_H_PT}" '
        f'font-family="Helvetica,Arial,sans-serif">'
    )

    # ---- Background paper (slightly warm off-white)
    out.append(f'<rect width="{POSTER_W_PT}" height="{POSTER_H_PT}" fill="{COLOR_BG}"/>')

    # ---- Landuse polygons (tier-ordered, low → high so playgrounds paint over parks)
    out.append('<g id="landuse">')
    for poly, cls in sorted(landuse_polys, key=lambda p: LANDUSE_STYLES[p[1]]["tier"]):
        style = LANDUSE_STYLES[cls]
        polys = [poly] if poly.geom_type == "Polygon" else list(poly.geoms)
        for p in polys:
            d = path_d_from_polygon(p, to_svg)
            out.append(
                f'<path d="{d}" fill="{style["fill"]}" fill-rule="evenodd"/>'
            )
    out.append('</g>')

    # ---- Streets: casings first, then road colors. Sort by tier.
    out.append('<g id="street-casings">')
    for w in sorted(highway_ways, key=lambda x: x["style"].get("tier", 0)):
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
    out.append('<g id="streets">')
    for w in sorted(highway_ways, key=lambda x: x["style"].get("tier", 0)):
        st = w["style"]
        d = path_d_from_line(w["line"], to_svg)
        out.append(
            f'<path d="{d}" stroke="{st["color"]}" '
            f'stroke-width="{st["width"]}" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )
    out.append('</g>')

    # ---- Waterway lines (rivers/streams/canals). Drawn over land but under mask.
    out.append('<g id="waterways">')
    for line, kind in waterway_lines:
        st = WATERWAY_STYLES.get(kind, WATERWAY_STYLES["stream"])
        d = path_d_from_line(line, to_svg)
        out.append(
            f'<path d="{d}" stroke="{st["color"]}" stroke-width="{st["width"]}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    out.append('</g>')

    # ---- World mask: dim everything outside the district (over color, under boundary)
    mask_d = world_mask_path_d(district_utm, to_svg)
    out.append(
        f'<path id="world-mask" d="{mask_d}" fill="{MASK_FILL}" '
        f'fill-opacity="{MASK_OPACITY}" fill-rule="evenodd"/>'
    )

    # ---- District boundary (thin solid red, no casing — just an indicator)
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
        f'<path id="boundary-line" d="{boundary_d}" '
        f'stroke="{COLOR_BOUNDARY}" stroke-width="{BOUNDARY_WIDTH}" '
        f'fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # ---- Labels via textPath (each label curves along its road)
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
            "halo": COLOR_BG,
            "halo_width": 2.0 if is_major else 1.2,
            "weight": 600 if is_major else 500,
            "priority": (10 if is_major else 0)
            + sum(ls.length for ls in bucket["lines"]) / 100.0,
        })
    labels = place_labels(streets_for_label, to_svg)

    # Emit a single <defs> block with all label paths
    out.append('<defs>')
    for lbl in labels:
        out.append(f'<path id="{lbl["def_id"]}" d="{lbl["def_path_d"]}"/>')
    out.append('</defs>')

    out.append('<g id="labels">')
    for lbl in labels:
        out.append(
            f'<text font-size="{lbl["size"]}" font-weight="{lbl["weight"]}" '
            f'fill="{lbl["color"]}" stroke="{lbl["halo"]}" '
            f'stroke-width="{lbl["halo_width"]}" '
            f'paint-order="stroke" stroke-linejoin="round">'
            f'<textPath xlink:href="#{lbl["def_id"]}" startOffset="50%" '
            f'text-anchor="middle">{xml_escape(lbl["text"])}</textPath>'
            f'</text>'
        )
    out.append('</g>')

    # ---- Header
    rule_y = HEADER_HEIGHT_PT
    out.append(
        f'<g id="header">'
        f'<rect x="0" y="0" width="{POSTER_W_PT}" height="{HEADER_HEIGHT_PT}" fill="{COLOR_BG}"/>'
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
        f'<rect x="0" y="{foot_y}" width="{POSTER_W_PT}" height="{FOOTER_HEIGHT_PT}" fill="{COLOR_BG}"/>'
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
    parser.add_argument("district", type=int)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    base = PROJECT_ROOT / "public" / "data" / f"candidate-district-{args.district}"
    boundary_path = base / "district-boundary.geojson"
    labels_path = base / "print-street-labels.json"
    out_path = args.out or (base / "print-map.svg")
    # New cache filename — broader query than the highway-only one. The old
    # district-{n}-all-highways.json cache is left alone for the JSON pipeline.
    cache_path = PROJECT_ROOT / ".cache" / "overpass" / f"district-{args.district}-features.json"

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

    minx, miny, maxx, maxy = district_wgs.bounds
    query = overpass_query(miny, minx, maxy, maxx)
    payload = fetch_overpass(query, cache_path, force=args.force_refresh)

    print(f"[district {args.district}] aggregating features…", file=sys.stderr)
    highway_ways, landuse_polys, waterway_lines, by_name = aggregate_features(
        payload, district_utm
    )
    print(
        f"[district {args.district}] {len(highway_ways)} highway segments, "
        f"{len(landuse_polys)} landuse polygons, {len(waterway_lines)} waterways, "
        f"{len(by_name)} unique street names",
        file=sys.stderr,
    )

    labels_data = json.loads(labels_path.read_text())
    allowlist = labels_data.get("allowlist", [])

    svg = render_svg(args.district, district_utm, highway_ways, landuse_polys,
                     waterway_lines, by_name, allowlist)
    out_path.write_text(svg)

    size_kb = out_path.stat().st_size / 1024
    label_count = svg.count("<textPath")
    print(
        f"[out] wrote {out_path}\n"
        f"      {size_kb:,.0f} KB  ({size_kb / 1024:.1f} MB)\n"
        f"      {label_count} curved labels placed",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
