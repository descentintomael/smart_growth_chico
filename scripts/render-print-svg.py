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
    Point,
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
# Title block uses a humanist serif for civic weight without being institutional.
# Body, labels, and chrome stay in a clean grotesque sans for legibility at scale.
FONT_SERIF = "Georgia, Cambria, 'Times New Roman', serif"
FONT_SANS = "Helvetica, Arial, sans-serif"

TITLE_PT = 80          # bumped — title now carries more visual weight
SUBTITLE_PT = 22
TAGLINE_PT = 14
FOOTER_PT = 14         # bumped from 12 per accessibility review

LABEL_MAJOR_PT = 14
LABEL_MINOR_PT = 9     # bumped from 7 per accessibility review (Vikram)
LABEL_PLACE_PT = 18    # park / school names — italic, sits above street labels
LABEL_SHIELD_PT = 13

# Header / footer
COLOR_TITLE = "#0f172a"
COLOR_SUBTITLE = "#525252"
COLOR_TAGLINE = "#6b7280"
COLOR_FOOTER = "#6b7280"
COLOR_RULE = "#d4d4d4"
COLOR_ACCENT = "#1e3a8a"  # navy accent band, matches boundary

# Place-name label colors
COLOR_PARK_LABEL = "#3f6212"      # lime-800 — feels like greenery, not text
COLOR_SCHOOL_LABEL = "#854d0e"    # amber-800
COLOR_WATER_LABEL = "#1e40af"     # blue-800
COLOR_PLACE_HALO = "#fbfaf6"      # paper background

# Paper background — slightly warm off-white so the poster feels printed,
# not screen-bright. Subtle enough that pastels still pop.
COLOR_BG = "#fbfaf6"

# District boundary — civic navy, not red. Buffered outward a few meters so it
# clears edge-running roads (Bruce Rd, E 20th, etc.) instead of overlapping them.
COLOR_BOUNDARY = "#1e3a8a"  # indigo-900; reads as civic / official, not alarming
BOUNDARY_WIDTH = 4.0          # bumped from 2.0 — needed visual presence
BOUNDARY_CASING_WIDTH = 7.0
BOUNDARY_CASING_COLOR = COLOR_BG
BOUNDARY_BUFFER_M = 15

# World mask — fades everything outside the district. We use the paper color
# (not pure white) so the mask blends with the page and the fade looks uniform.
MASK_FILL = COLOR_BG
MASK_OPACITY = 0.86  # used for the outermost cap; the fade rings ramp up to this

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

# Highway shield styling. The shield "kind" is inferred from the ref's network
# tag if present, otherwise from the ref string itself.
#
# `path` is the SVG path centered at (0,0). It defines the silhouette of the
# shield — US routes use the classic curved-shield silhouette; California state
# routes use a pentagon ("spade") matching the real signage; interstates use a
# shield shape similar to US.
SHIELD_STYLES = {
    # US Highway: classic shield with curved top, pointed bottom.
    "us": {
        "fill": "#ffffff", "stroke": "#111827", "text": "#111827",
        "width": 38, "height": 36, "text_dy": 2,
        "path": "M-19,-12 Q-19,-18 -13,-18 H13 Q19,-18 19,-12 V6 Q19,9 15,12 L0,18 L-15,12 Q-19,9 -19,6 Z",
    },
    # Interstate: shield with blue body + red top bar (rendered separately).
    "i": {
        "fill": "#1e3a8a", "stroke": "#0f172a", "text": "#ffffff",
        "width": 38, "height": 36, "text_dy": 4,
        "path": "M-19,-12 Q-19,-18 -13,-18 H13 Q19,-18 19,-12 V6 Q19,9 15,12 L0,18 L-15,12 Q-19,9 -19,6 Z",
        "top_band_h": 7, "top_fill": "#b91c1c",
    },
    # CA State Route: green pentagon (the "spade" silhouette real signs use).
    "state": {
        "fill": "#15803d", "stroke": "#052e16", "text": "#ffffff",
        "width": 36, "height": 38, "text_dy": 1,
        "path": "M-18,-14 Q-18,-19 -13,-19 H13 Q18,-19 18,-14 V4 L0,19 L-18,4 Z",
    },
    # Unknown route — small rounded card.
    "generic": {
        "fill": "#ffffff", "stroke": "#111827", "text": "#111827",
        "width": 32, "height": 26, "text_dy": 0,
        "path": "M-16,-13 Q-16,-13 -16,-11 H16 Q16,-13 16,-13 V11 Q16,13 14,13 H-14 Q-16,13 -16,11 Z",
    },
}

# Map fade — overlapping paper-colored layers that ramp aggressively at the
# boundary, then taper. Each entry is
# (distance-from-buffered-boundary-meters, per-layer fade-opacity). Each layer
# is rendered as "everything outside this buffered polygon" so they STACK.
#
# Tuned for: ~60% fade right at the boundary (dramatic drop), ~75% at 200m,
# ~88% at the far edge.
FADE_LAYERS = [
    (0,    0.60),  # immediate hard drop at the boundary
    (50,   0.12),
    (130,  0.12),
    (260,  0.12),
    (440,  0.12),
    (680,  0.15),
    (1000, 0.18),
    (1500, 0.22),
]


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
    """Build an evenodd path: world rectangle MINUS district exterior PLUS
    district interior holes.

    With evenodd:
      - Outer rect:     fill IN     (1 crossing)
      - District ext:   fill OUT    (2 crossings — district interior is unmasked)
      - District holes: fill IN     (3 crossings — sub-district carve-outs ARE masked)
    """
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

    polys = (
        [district_utm] if district_utm.geom_type == "Polygon"
        else list(district_utm.geoms)
    )
    for poly in polys:
        # Exterior: punches a hole in the world mask (the district interior
        # remains unmasked).
        ext = list(poly.exterior.coords)
        svg_pts = [to_svg(x, y) for x, y in ext]
        parts.append(f"M{svg_pts[0][0]:.1f},{svg_pts[0][1]:.1f}")
        for x, y in svg_pts[1:]:
            parts.append(f"L{x:.1f},{y:.1f}")
        parts.append("Z")
        # Interior rings (carve-outs of other districts): re-fill so they ARE
        # masked alongside the rest of the outside-world. Evenodd handles the
        # alternation automatically.
        for interior in poly.interiors:
            int_coords = list(interior.coords)
            svg_pts = [to_svg(x, y) for x, y in int_coords]
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

def shield_kind_for(ref: str, network: str | None) -> str:
    """Decide which shield style a ref string should use."""
    if network:
        n = network.lower()
        if "interstate" in n or n == "us:i":
            return "i"
        if "us:" in n or "us-highway" in n:
            return "us"
        if "us:ca" in n or "ca:" in n:
            return "state"
    r = ref.strip().upper()
    if r.startswith("I "):
        return "i"
    if r.startswith("US "):
        return "us"
    if r.startswith("CA ") or r.startswith("SR ") or r.startswith("CA-"):
        return "state"
    # Bare number — assume state route in our CA context.
    if r.replace("-", " ").split()[0].isdigit():
        return "state"
    return "generic"


def aggregate_features(payload, district_utm):
    """Return aggregated features and lookup structures.

    Returns:
        highway_ways: list of {"line", "class", "style"}
        landuse_polys: list of {"poly", "class", "name"}
        waterway_lines: list of (line, kind, name)
        by_name: dict[name] = {"lines": [...], "classes": {...}, "refs": {...}}
        refs: dict[ref] = {"lines": [...], "kind": "us"|"state"|..., "network": str}
    """
    context = district_utm.buffer(800)

    highway_ways = []
    landuse_polys = []
    waterway_lines = []
    by_name = {}
    refs = {}

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
            name = tags.get("name")
            lines_to_add = (
                [clipped] if clipped.geom_type == "LineString"
                else list(clipped.geoms) if clipped.geom_type == "MultiLineString"
                else []
            )
            for sub in lines_to_add:
                waterway_lines.append((sub, waterway, name))
            continue

        # ---- Landuse / zones ----
        cls = classify_landuse(tags)
        if cls is not None and cls in LANDUSE_STYLES:
            poly_utm = way_to_utm_polygon(el)
            if poly_utm is None:
                continue
            clipped = poly_utm.intersection(context)
            if clipped.is_empty:
                continue
            name = tags.get("name")
            polys = (
                [clipped] if clipped.geom_type == "Polygon"
                else list(clipped.geoms) if clipped.geom_type == "MultiPolygon"
                else []
            )
            for p in polys:
                landuse_polys.append({"poly": p, "class": cls, "name": name})
            if not tags.get("highway"):
                continue

        # ---- Highways ----
        highway = tags.get("highway")
        if highway is None:
            continue
        # Skip service roads — parking aisles and driveways add clutter at
        # poster scale without helping residents navigate.
        if highway == "service":
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
        lines = (
            [clipped] if clipped.geom_type == "LineString"
            else list(clipped.geoms) if clipped.geom_type == "MultiLineString"
            else []
        )
        for ls in lines:
            highway_ways.append({"line": ls, "class": highway, "style": style})
            name = tags.get("name")
            if name:
                bucket = by_name.setdefault(
                    name, {"lines": [], "classes": set()}
                )
                bucket["lines"].append(ls)
                bucket["classes"].add(highway)

        # Route refs (for shield rendering). One way may carry multiple refs
        # separated by ";".
        ref_value = tags.get("ref")
        network = tags.get("network")
        if ref_value and highway in MAJOR_CLASSES:
            for ref in [r.strip() for r in ref_value.split(";") if r.strip()]:
                bucket = refs.setdefault(
                    ref, {"lines": [], "kind": shield_kind_for(ref, network), "network": network or ""}
                )
                for ls in lines:
                    bucket["lines"].append(ls)

    return highway_ways, landuse_polys, waterway_lines, by_name, refs


# ====================== Chrome elements (scale, north, shields, places) ======================

def render_scale_bar(x_right: float, y_bottom: float, scale_pt_per_m: float) -> str:
    """Render a 1-mile scale bar with quarter-mile ticks at (x_right, y_bottom).

    Coordinates point to the BOTTOM-RIGHT corner of the bar; it extends leftward
    and upward from there.
    """
    METERS_PER_MILE = 1609.344
    one_mile_pt = METERS_PER_MILE * scale_pt_per_m
    bar_h = 6
    text_pt = 10
    label_pad = 4

    x0 = x_right - one_mile_pt
    y_top = y_bottom - bar_h
    parts = ['<g id="scale-bar">']
    # Alternating black/white quarter-mile segments make the scale readable
    # without needing color cues.
    segments = 4
    seg_w = one_mile_pt / segments
    for i in range(segments):
        fill = "#0f172a" if i % 2 == 0 else "#ffffff"
        parts.append(
            f'<rect x="{x0 + i * seg_w:.1f}" y="{y_top:.1f}" '
            f'width="{seg_w:.1f}" height="{bar_h}" fill="{fill}" '
            f'stroke="#0f172a" stroke-width="0.5"/>'
        )
    # Tick labels
    for tick_mi, x in [
        (0,    x0),
        (0.25, x0 + 0.25 * one_mile_pt),
        (0.5,  x0 + 0.5 * one_mile_pt),
        (1.0,  x_right),
    ]:
        label = "0" if tick_mi == 0 else (f"{tick_mi:g} mi" if tick_mi == 1 else f"{tick_mi:g}")
        parts.append(
            f'<text x="{x:.1f}" y="{y_top - label_pad:.1f}" '
            f'font-family="{FONT_SANS}" font-size="{text_pt}" '
            f'text-anchor="middle" fill="#0f172a">{label}</text>'
        )
    parts.append('</g>')
    return "\n".join(parts)


def render_north_arrow(cx: float, cy: float, r: float = 20) -> str:
    """A minimalist compass arrow inside a thin circle."""
    head = (cx, cy - r * 0.7)
    left = (cx - r * 0.35, cy + r * 0.35)
    right = (cx + r * 0.35, cy + r * 0.35)
    notch = (cx, cy + r * 0.05)
    parts = [
        '<g id="north-arrow">',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" stroke="#0f172a" stroke-width="1"/>',
        # Filled (north) half
        f'<polygon points="{head[0]:.1f},{head[1]:.1f} {left[0]:.1f},{left[1]:.1f} {notch[0]:.1f},{notch[1]:.1f}" '
        f'fill="{COLOR_ACCENT}"/>',
        # Outlined (south) half
        f'<polygon points="{head[0]:.1f},{head[1]:.1f} {right[0]:.1f},{right[1]:.1f} {notch[0]:.1f},{notch[1]:.1f}" '
        f'fill="#ffffff" stroke="{COLOR_ACCENT}" stroke-width="1"/>',
        f'<text x="{cx}" y="{cy - r - 4}" font-family="{FONT_SANS}" font-size="11" '
        f'font-weight="700" text-anchor="middle" fill="#0f172a">N</text>',
        '</g>',
    ]
    return "\n".join(parts)


def shield_svg(cx: float, cy: float, ref: str, kind: str) -> str:
    """Render a route shield centered at (cx, cy) using the kind-specific path."""
    style = SHIELD_STYLES.get(kind, SHIELD_STYLES["generic"])
    # Strip the network prefix for display ("CA 32" → "32", "US 99" → "99")
    display = ref
    parts = display.split()
    if len(parts) > 1 and parts[0].upper() in ("US", "CA", "SR", "I"):
        display = parts[-1]

    # The shield path is in local coordinates; translate to (cx, cy).
    inner = [
        f'<path d="{style["path"]}" fill="{style["fill"]}" '
        f'stroke="{style["stroke"]}" stroke-width="1.4" stroke-linejoin="round"/>'
    ]
    # Interstate-style top band (red over blue shield)
    if "top_band_h" in style:
        band_h = style["top_band_h"]
        # Approximate the top band as a clipped rect over the upper portion.
        inner.append(
            f'<rect x="-19" y="-18" width="38" height="{band_h}" '
            f'fill="{style["top_fill"]}"/>'
        )
        # Re-stroke the outer path so the band edges look clean
        inner.append(
            f'<path d="{style["path"]}" fill="none" '
            f'stroke="{style["stroke"]}" stroke-width="1.4"/>'
        )
    text_dy = style.get("text_dy", 0)
    inner.append(
        f'<text x="0" y="{text_dy}" font-family="{FONT_SANS}" '
        f'font-size="{LABEL_SHIELD_PT}" font-weight="700" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'fill="{style["text"]}">{xml_escape(display)}</text>'
    )
    return (
        f'<g class="shield" transform="translate({cx:.1f},{cy:.1f})">'
        + "".join(inner)
        + '</g>'
    )


def place_shields(refs, to_svg, label_collision_bboxes):
    """Place one shield per ref at the midpoint of the longest segment.

    Avoids overlap with already-placed street labels via the supplied bbox list.
    Returns SVG <g> string + updated bbox list (mutated in place).
    """
    parts = []
    # Sort by combined route-line length (longer = more visible = label first)
    items = []
    for ref, b in refs.items():
        total = sum(l.length for l in b["lines"])
        items.append((ref, b, total))
    items.sort(key=lambda x: -x[2])

    for ref, b, _ in items:
        longest = max(b["lines"], key=lambda l: l.length)
        midpoint = longest.interpolate(0.5, normalized=True)
        cx, cy = to_svg(midpoint.x, midpoint.y)
        # Shield bbox
        style = SHIELD_STYLES.get(b["kind"], SHIELD_STYLES["generic"])
        w, h = style["width"], style["height"]
        bbox = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        if any(rect_overlap(bbox, ob) for ob in label_collision_bboxes):
            continue
        parts.append(shield_svg(cx, cy, ref, b["kind"]))
        label_collision_bboxes.append(bbox)
    return "\n".join(parts)


# Names we never want to label — these are activities inside larger features,
# not parks worth their own label at poster scale.
SKIP_NAME_PATTERNS = (
    "paragliding",
    "hang gliding",
    "landing zone",
    "launch",
)


def _emit_place_label(name, cx, cy, color, size) -> str:
    return (
        f'<text x="{cx:.1f}" y="{cy:.1f}" '
        f'font-family="{FONT_SERIF}" font-size="{size}" font-style="italic" '
        f'font-weight="500" text-anchor="middle" dominant-baseline="middle" '
        f'fill="{color}" stroke="{COLOR_PLACE_HALO}" stroke-width="2" '
        f'paint-order="stroke" stroke-linejoin="round">{xml_escape(name)}</text>'
    )


def _candidate_anchors_within(poly, base_anchor):
    """Yield (utm_x, utm_y) anchor candidates: representative_point first,
    then a ring of offsets inside the polygon at increasing radii.

    Used so labels for adjacent polygons (Marsh / Little Chico Creek; Pleasant
    Valley / Marigold) can find a non-overlapping spot inside their own polygon
    instead of getting killed by their neighbor's bbox.
    """
    yield (base_anchor.x, base_anchor.y)
    minx, miny, maxx, maxy = poly.bounds
    # Try offsets in cardinal + diagonal directions at multiple radii (meters)
    for radius_m in (50, 100, 160, 240):
        for dx, dy in (
            (0, -radius_m), (0, radius_m),
            (-radius_m, 0), (radius_m, 0),
            (-radius_m * 0.7, -radius_m * 0.7),
            (radius_m * 0.7, -radius_m * 0.7),
            (-radius_m * 0.7, radius_m * 0.7),
            (radius_m * 0.7, radius_m * 0.7),
        ):
            x = base_anchor.x + dx
            y = base_anchor.y + dy
            if minx <= x <= maxx and miny <= y <= maxy and poly.contains(Point(x, y)):
                yield (x, y)


def place_landuse_labels(landuse_polys, district_utm, to_svg, label_collision_bboxes):
    """Label parks, schools, and water bodies with class-aware rules.

    Schools are processed FIRST and use a multi-position search inside their
    polygon — when the representative-point would collide with an adjacent
    school's bbox (Little Chico Creek vs Marsh; Marigold vs Pleasant Valley),
    we walk a ring of UTM offsets and use the first non-colliding position.

    Schools use a wider 800m inclusion radius so nearby schools just outside
    the district line still appear as navigation landmarks.
    """
    parts = []
    interior_tight = district_utm.buffer(50)
    interior_schools = district_utm.buffer(800)
    placed_polys = []
    PARK_SPACING_PT = 220
    WATER_SPACING_PT = 160
    placed_anchors = []  # only used for parks/water proximity (schools rely on
                         # bbox collision via the multi-anchor search)

    def try_place(lu, color, size, spacing, interior_buf, use_multi_anchor=False):
        nonlocal parts
        poly = lu["poly"]
        name = lu["name"]
        if not poly.intersects(interior_buf):
            return False
        if any(p in name.lower() for p in SKIP_NAME_PATTERNS):
            return False
        if len(name) > 40:
            return False
        anchor = poly.representative_point()
        # Sub-feature dedup (Goose Cove inside Bidwell, etc.) still applies.
        if any(
            placed_poly.contains(anchor) or placed_poly.contains(poly.centroid)
            for placed_poly in placed_polys
        ):
            return False

        label_w = estimate_text_width_pt(name, size)
        label_h = size * 1.2

        # Candidate anchors: rep-point first, then ring search if the call site
        # asked for multi-anchor placement (schools), single-shot otherwise.
        if use_multi_anchor:
            candidates = list(_candidate_anchors_within(poly, anchor))
        else:
            candidates = [(anchor.x, anchor.y)]

        for utm_x, utm_y in candidates:
            cx, cy = to_svg(utm_x, utm_y)
            # Spacing test (single proximity check for non-school classes).
            if not use_multi_anchor and spacing > 0:
                too_close = any(
                    ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5 < spacing
                    for (px, py, _) in placed_anchors
                )
                if too_close:
                    return False
            bbox = (cx - label_w / 2, cy - label_h / 2,
                    cx + label_w / 2, cy + label_h / 2)
            if any(rect_overlap(bbox, ob) for ob in label_collision_bboxes):
                continue
            parts.append(_emit_place_label(name, cx, cy, color, size))
            label_collision_bboxes.append(bbox)
            placed_polys.append(poly)
            placed_anchors.append((cx, cy, lu["class"]))
            return True
        return False

    named = [lu for lu in landuse_polys if lu.get("name")]

    # ---- Schools first (use wider 800m radius so nearby schools just outside
    #      the district still appear as navigation landmarks)
    schools = sorted(
        [lu for lu in named if lu["class"] == "school"],
        key=lambda lu: -lu["poly"].area,
    )
    for lu in schools:
        # use_multi_anchor=True lets schools find an alternate position inside
        # their polygon when their representative-point bbox collides.
        try_place(lu, COLOR_SCHOOL_LABEL, LABEL_PLACE_PT, 0, interior_schools,
                  use_multi_anchor=True)

    # ---- Parks (umbrella features first so Bidwell beats sub-cove names)
    parks = sorted(
        [lu for lu in named if lu["class"] in
         ("park", "grass", "forest", "cemetery", "sports", "playground")],
        key=lambda lu: -lu["poly"].area,
    )
    for lu in parks:
        try_place(lu, COLOR_PARK_LABEL, LABEL_PLACE_PT, PARK_SPACING_PT, interior_tight,
                  use_multi_anchor=False)

    # ---- Water last
    waters = sorted(
        [lu for lu in named if lu["class"] == "water"],
        key=lambda lu: -lu["poly"].area,
    )
    for lu in waters:
        try_place(lu, COLOR_WATER_LABEL, LABEL_PLACE_PT, WATER_SPACING_PT, interior_tight,
                  use_multi_anchor=False)

    return "\n".join(parts)


def buffer_exterior_keep_holes(polygon, dist_m):
    """Buffer the polygon's exterior outward by dist_m but keep its interior
    holes at their ORIGINAL size.

    Standard shapely.buffer(d) shrinks interior holes by d as well — which is
    wrong for our fade mask. A peninsula carve-out 250m across vanishes after a
    layer with buffer 250m+, and the entire peninsula starts being treated as
    "inside the district" by that layer. This helper preserves the holes so
    every fade layer's geometry has the same interior structure.
    """
    polys = (
        [polygon] if polygon.geom_type == "Polygon"
        else list(polygon.geoms)
    )
    result_polys = []
    for p in polys:
        ext_only = Polygon(p.exterior.coords)
        buffered_ext = ext_only.buffer(dist_m)
        for interior in p.interiors:
            hole = Polygon(interior.coords)
            buffered_ext = buffered_ext.difference(hole)
        if buffered_ext.is_empty:
            continue
        if buffered_ext.geom_type == "Polygon":
            result_polys.append(buffered_ext)
        else:
            result_polys.extend(buffered_ext.geoms)
    if not result_polys:
        return polygon
    return unary_union(result_polys)


def fade_rings_svg(district_utm, to_svg, buffer_base_m: float) -> str:
    """Stack of overlapping paper-colored "outside" masks producing a soft fade.

    Each layer covers *everything outside* the (exterior-buffered, holes-kept)
    polygon and extends to the canvas edge. Layers overlap, so cumulative
    opacity at a point P is `1 - product(1 - layer_opacity_i for layers whose
    inner edge is closer to the district than P)`. Near the boundary one layer
    covers (light fade); far away every layer covers (deep fade). Result:
    smooth gradient AND uniform coverage of interior carve-outs.
    """
    parts = ['<g id="fade-mask">']
    for dist_m, opacity in FADE_LAYERS:
        buf = buffer_exterior_keep_holes(district_utm, buffer_base_m + dist_m)
        d = world_mask_path_d(buf, to_svg)
        parts.append(
            f'<path d="{d}" fill="{MASK_FILL}" fill-opacity="{opacity}" '
            f'fill-rule="evenodd"/>'
        )
    parts.append('</g>')
    return "\n".join(parts)


# ====================== SVG assembly ======================

def render_svg(district_n, district_utm, highway_ways, landuse_polys, waterway_lines, by_name, refs, allowlist, stats=None):
    to_svg, scale_pt_per_m = make_utm_to_svg(district_utm)

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{POSTER_W_IN}in" height="{POSTER_H_IN}in" '
        f'viewBox="0 0 {POSTER_W_PT} {POSTER_H_PT}" '
        f'font-family="{FONT_SANS}">'
    )
    out.append(
        f'<title>Chico City Council District {district_n}</title>'
        f'<desc>Street-level reference map of Chico City Council District {district_n}.'
        f' Includes street network, district boundary, parks, schools, and waterways.</desc>'
    )

    # ---- Background paper (slightly warm off-white)
    out.append(f'<rect width="{POSTER_W_PT}" height="{POSTER_H_PT}" fill="{COLOR_BG}"/>')

    # ---- Landuse polygons (tier-ordered, low → high so playgrounds paint over parks)
    out.append('<g id="landuse">')
    for lu in sorted(landuse_polys, key=lambda p: LANDUSE_STYLES[p["class"]]["tier"]):
        style = LANDUSE_STYLES[lu["class"]]
        poly = lu["poly"]
        polys = [poly] if poly.geom_type == "Polygon" else list(poly.geoms)
        for p in polys:
            d = path_d_from_polygon(p, to_svg)
            out.append(f'<path d="{d}" fill="{style["fill"]}" fill-rule="evenodd"/>')
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

    # ---- Waterway lines
    out.append('<g id="waterways">')
    for line, kind, _name in waterway_lines:
        st = WATERWAY_STYLES.get(kind, WATERWAY_STYLES["stream"])
        d = path_d_from_line(line, to_svg)
        out.append(
            f'<path d="{d}" stroke="{st["color"]}" stroke-width="{st["width"]}" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    out.append('</g>')

    # ---- Soft fade rings (replaces the hard mask edge)
    boundary_poly = district_utm.buffer(BOUNDARY_BUFFER_M)
    out.append(fade_rings_svg(district_utm, to_svg, BOUNDARY_BUFFER_M))

    # ---- District boundary: a soft paper-colored casing under a navy line.
    # Drawn AFTER the fade so it isn't dimmed by the mask layers near the edge.
    # Includes interior holes (carve-outs of other districts) so the boundary
    # wraps around the peninsula areas too.
    boundary_paths = []
    boundary_polys = (
        [boundary_poly] if boundary_poly.geom_type == "Polygon"
        else list(boundary_poly.geoms)
    )
    rings = []
    for poly in boundary_polys:
        rings.append(list(poly.exterior.coords))
        for interior in poly.interiors:
            rings.append(list(interior.coords))
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
        f'stroke="{BOUNDARY_CASING_COLOR}" stroke-width="{BOUNDARY_CASING_WIDTH}" '
        f'fill="none" stroke-linejoin="round" stroke-linecap="round" opacity="0.85"/>'
    )
    out.append(
        f'<path id="boundary-line" d="{boundary_d}" '
        f'stroke="{COLOR_BOUNDARY}" stroke-width="{BOUNDARY_WIDTH}" '
        f'fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # ---- Street labels via textPath
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

    out.append('<defs>')
    for lbl in labels:
        out.append(f'<path id="{lbl["def_id"]}" d="{lbl["def_path_d"]}"/>')
    out.append('</defs>')

    out.append('<g id="street-labels">')
    for lbl in labels:
        out.append(
            f'<text font-family="{FONT_SANS}" font-size="{lbl["size"]}" '
            f'font-weight="{lbl["weight"]}" '
            f'fill="{lbl["color"]}" stroke="{lbl["halo"]}" '
            f'stroke-width="{lbl["halo_width"]}" '
            f'paint-order="stroke" stroke-linejoin="round">'
            f'<textPath xlink:href="#{lbl["def_id"]}" startOffset="50%" '
            f'text-anchor="middle">{xml_escape(lbl["text"])}</textPath>'
            f'</text>'
        )
    out.append('</g>')

    # Track bboxes for collision so place labels & shields don't overlap streets.
    street_bboxes = []  # we don't have these from place_labels — re-derive
    for lbl in labels:
        # Approximate: use the first segment of the path for the bbox
        # (the labels are textPath-based, so the curve runs along the road.)
        pass

    # ---- Place-name labels (parks, schools, water)
    place_labels_svg = place_landuse_labels(landuse_polys, district_utm, to_svg, street_bboxes)
    out.append(f'<g id="place-labels">{place_labels_svg}</g>')

    # ---- Highway shields
    shield_svg_block = place_shields(refs, to_svg, street_bboxes)
    out.append(f'<g id="shields">{shield_svg_block}</g>')

    # ---- Scale bar (bottom-right of map area, inside the page padding)
    scale_x = POSTER_W_PT - PAGE_PADDING_PT
    scale_y = MAP_BOTTOM - 24
    out.append(render_scale_bar(scale_x, scale_y, scale_pt_per_m))

    # ---- North arrow (top-right of map area)
    out.append(render_north_arrow(POSTER_W_PT - PAGE_PADDING_PT - 24,
                                   MAP_TOP + 50, r=22))

    # ---- Stats panel ("By the Numbers") in the right-side negative space
    if stats:
        # Count parks/open-space polygons that intersect the district interior
        parks_classes = {"park", "sports", "playground", "grass", "forest"}
        parks_count = sum(
            1 for lu in landuse_polys
            if lu["class"] in parks_classes and lu.get("name")
            and lu["poly"].intersects(district_utm)
        )
        panel_w = 460
        panel_x = POSTER_W_PT - PAGE_PADDING_PT - panel_w
        panel_y = MAP_TOP + 110
        out.append(render_stats_panel(stats, parks_count, panel_x, panel_y, panel_w))

    # ---- Header — civic poster title block
    out.append(render_header(district_n))

    # ---- Footer
    out.append(render_footer())

    out.append('</svg>')
    return "\n".join(out)


def render_header(district_n: int) -> str:
    """Title block with a navy accent band, serif title, italic subtitle, and
    a large district numeral on the right that gives the poster strong identity."""
    accent_h = 12
    rule_y = HEADER_HEIGHT_PT
    title_baseline_y = 110
    subtitle_y = 146
    tagline_y = 178

    # Big district numeral on the right side of the header — gives the poster
    # an immediate "this is District 6" identity element.
    numeral_r = 78
    circle_cy = (HEADER_HEIGHT_PT + accent_h) / 2
    numeral_x = POSTER_W_PT - PAGE_PADDING_PT - numeral_r - 8
    numeral_fs = int(numeral_r * 1.25)
    # When using dominant-baseline=central, Georgia's specific metrics still
    # render slightly high on most renderers (the "central" anchor is at the
    # font's central baseline, but the visual center of a numeral sits a bit
    # below that). A small downward nudge centers it visually.
    numeral_y_nudge = numeral_fs * 0.06

    return (
        f'<g id="header">'
        # Top accent bar
        f'<rect x="0" y="0" width="{POSTER_W_PT}" height="{accent_h}" fill="{COLOR_ACCENT}"/>'
        # Background fill below accent
        f'<rect x="0" y="{accent_h}" width="{POSTER_W_PT}" height="{HEADER_HEIGHT_PT - accent_h}" fill="{COLOR_BG}"/>'
        # Title (serif, generous size, slight letterspacing)
        f'<text x="{PAGE_PADDING_PT}" y="{title_baseline_y}" '
        f'font-family="{FONT_SERIF}" font-size="{TITLE_PT}" font-weight="700" '
        f'fill="{COLOR_TITLE}" letter-spacing="0.5">Chico City Council</text>'
        # Subtitle line: "District N"  + italic descriptor
        f'<text x="{PAGE_PADDING_PT}" y="{subtitle_y}" '
        f'font-family="{FONT_SERIF}" font-size="{SUBTITLE_PT}" font-style="italic" '
        f'fill="{COLOR_SUBTITLE}">District {district_n} — A resident\'s reference</text>'
        # Tagline (sans, lighter)
        f'<text x="{PAGE_PADDING_PT}" y="{tagline_y}" '
        f'font-family="{FONT_SANS}" font-size="{TAGLINE_PT}" font-weight="400" '
        f'fill="{COLOR_TAGLINE}">Streets, parks, schools, and waterways</text>'
        # Numeral badge — outlined circle with district number, vertically
        # centered via dominant-baseline=central plus a small visual nudge.
        f'<circle cx="{numeral_x}" cy="{circle_cy}" r="{numeral_r}" '
        f'fill="none" stroke="{COLOR_ACCENT}" stroke-width="3"/>'
        f'<text x="{numeral_x}" y="{circle_cy + numeral_y_nudge:.1f}" '
        f'font-family="{FONT_SERIF}" font-size="{numeral_fs}" font-weight="700" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'fill="{COLOR_ACCENT}">{district_n}</text>'
        # Bottom rule
        f'<line x1="0" y1="{rule_y}" x2="{POSTER_W_PT}" y2="{rule_y}" '
        f'stroke="{COLOR_RULE}" stroke-width="0.75"/>'
        f'</g>'
    )


def render_stats_panel(stats: dict, parks_count: int, x_left: float, y_top: float,
                        width: float) -> str:
    """A "By the Numbers" panel for the right-side negative space.

    Three sections, in order: District overview, Local businesses, Community
    infrastructure. Uses serif heading + caps-eyebrow label + right-aligned
    figure style for that civic-document feel.
    """
    demo = stats.get("demographics") or {}
    biz = (stats.get("businesses") or {}).get("by_bucket", {})

    population = demo.get("population", 0)
    households = demo.get("households", 0)
    land_area = demo.get("land_area_sq_mi", 0)
    age = demo.get("age") or {}
    tenure_owner = demo.get("owner_occupied", 0)
    tenure_renter = demo.get("renter_occupied", 0)
    edu = demo.get("education_25plus") or {}
    edu_total = sum(edu.values()) or 1
    pct_bachelors = round(100 * (edu.get("bachelors", 0) + edu.get("graduate", 0)) / edu_total)

    # Layout constants
    padding = 24
    title_pt = 24
    section_pt = 13
    label_pt = 11
    figure_pt = 18
    line_h_section = section_pt * 1.4
    line_h_row = 26
    line_h_section_gap = 18
    rule_w = 0.75

    # Build content rows. Each row: (LABEL CAPS, value text)
    overview = [
        ("Population", f"{population:,}"),
        ("Households", f"{households:,}"),
        ("Land area", f"{land_area} sq mi"),
        ("Owner / renter", f"{tenure_owner:,} / {tenure_renter:,}"),
        ("College degree (25+)", f"{pct_bachelors}%"),
    ]
    businesses = [
        ("Restaurants & cafés",   biz.get("food_and_drink", 0)),
        ("Retail shops",          biz.get("retail", 0)),
        ("Grocery & markets",     biz.get("grocery", 0)),
        ("Medical offices",       biz.get("medical", 0)),
        ("Hospitality",           biz.get("hospitality", 0)),
        ("Cultural & arts",       biz.get("cultural", 0)),
    ]
    # Drop categories with 0 count to keep the panel honest
    businesses = [b for b in businesses if b[1] > 0]
    businesses = [(label, f"{count}") for label, count in businesses]
    community = [
        ("Public schools",        biz.get("schools", 0)),
        ("Civic facilities",      biz.get("civic", 0)),
        ("Parks & open space",    parks_count),
    ]
    community = [(label, f"{count}") for label, count in community if count > 0]

    sections = [
        ("Overview",          overview),
        ("Local businesses",  businesses),
        ("Community",         community),
    ]

    # Compute total panel height
    body_h = padding * 2  # top + bottom padding
    body_h += title_pt + 8  # title block
    body_h += rule_w + line_h_section_gap
    for section_name, rows in sections:
        body_h += line_h_section + 4
        body_h += rule_w + 6
        body_h += line_h_row * len(rows)
        body_h += line_h_section_gap

    panel_x = x_left
    panel_y = y_top
    panel_w = width
    panel_h = body_h

    parts = ['<g id="stats-panel">']
    # Background — subtle paper card with thin navy stroke
    parts.append(
        f'<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="{panel_h}" '
        f'rx="6" ry="6" fill="{COLOR_BG}" stroke="{COLOR_ACCENT}" '
        f'stroke-opacity="0.45" stroke-width="0.8"/>'
    )

    # Top accent strip
    parts.append(
        f'<rect x="{panel_x}" y="{panel_y}" width="{panel_w}" height="4" '
        f'rx="6" ry="6" fill="{COLOR_ACCENT}"/>'
    )

    cx = panel_x + padding
    cy = panel_y + padding + title_pt

    # Title
    parts.append(
        f'<text x="{cx}" y="{cy}" font-family="{FONT_SERIF}" '
        f'font-size="{title_pt}" font-weight="700" fill="{COLOR_TITLE}">'
        f'By the Numbers</text>'
    )
    cy += 8

    # Sections
    for section_name, rows in sections:
        cy += line_h_section
        parts.append(
            f'<text x="{cx}" y="{cy}" font-family="{FONT_SANS}" '
            f'font-size="{section_pt}" font-weight="700" '
            f'fill="{COLOR_ACCENT}" letter-spacing="1.5">'
            f'{section_name.upper()}</text>'
        )
        cy += 4
        # Thin section underline
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{panel_x + panel_w - padding}" '
            f'y2="{cy}" stroke="{COLOR_ACCENT}" stroke-opacity="0.3" '
            f'stroke-width="{rule_w}"/>'
        )
        cy += 8
        for label, value in rows:
            row_y = cy + label_pt
            parts.append(
                f'<text x="{cx}" y="{row_y}" font-family="{FONT_SANS}" '
                f'font-size="{label_pt}" font-weight="400" fill="{COLOR_SUBTITLE}">'
                f'{xml_escape(label)}</text>'
            )
            parts.append(
                f'<text x="{panel_x + panel_w - padding}" y="{row_y + 1}" '
                f'font-family="{FONT_SERIF}" font-size="{figure_pt}" '
                f'font-weight="600" text-anchor="end" fill="{COLOR_TITLE}">'
                f'{xml_escape(value)}</text>'
            )
            cy += line_h_row
        cy += line_h_section_gap - line_h_row + 4

    parts.append('</g>')
    return "\n".join(parts)


def render_footer() -> str:
    foot_y = MAP_BOTTOM
    date_str = datetime.now(timezone.utc).date().isoformat()
    return (
        f'<g id="footer">'
        f'<rect x="0" y="{foot_y}" width="{POSTER_W_PT}" height="{FOOTER_HEIGHT_PT}" fill="{COLOR_BG}"/>'
        f'<line x1="0" y1="{foot_y}" x2="{POSTER_W_PT}" y2="{foot_y}" '
        f'stroke="{COLOR_RULE}" stroke-width="0.75"/>'
        f'<text x="{PAGE_PADDING_PT}" y="{foot_y + FOOTER_HEIGHT_PT / 2}" '
        f'font-family="{FONT_SANS}" font-size="{FOOTER_PT}" fill="{COLOR_FOOTER}" '
        f'dominant-baseline="middle">Data: OpenStreetMap contributors · City of Chico</text>'
        f'<text x="{POSTER_W_PT - PAGE_PADDING_PT}" y="{foot_y + FOOTER_HEIGHT_PT / 2}" '
        f'font-family="{FONT_SANS}" font-size="{FOOTER_PT}" fill="{COLOR_FOOTER}" '
        f'text-anchor="end" dominant-baseline="middle">Generated {date_str}</text>'
        f'</g>'
    )


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
    highway_ways, landuse_polys, waterway_lines, by_name, refs = aggregate_features(
        payload, district_utm
    )
    print(
        f"[district {args.district}] {len(highway_ways)} highway segments, "
        f"{len(landuse_polys)} landuse polygons, {len(waterway_lines)} waterways, "
        f"{len(by_name)} unique street names, {len(refs)} route refs",
        file=sys.stderr,
    )

    labels_data = json.loads(labels_path.read_text())
    allowlist = labels_data.get("allowlist", [])

    # Optional stats panel — present if aggregate-district-stats.py has been run.
    stats_path = base / "print-district-stats.json"
    stats = None
    if stats_path.exists():
        stats = json.loads(stats_path.read_text())
        print(f"[district {args.district}] stats panel: enabled (population "
              f"≈ {stats['demographics']['population']:,})", file=sys.stderr)
    else:
        print(f"[district {args.district}] stats panel: skipped "
              f"(no {stats_path.name} — run aggregate-district-stats.py)",
              file=sys.stderr)

    svg = render_svg(args.district, district_utm, highway_ways, landuse_polys,
                     waterway_lines, by_name, refs, allowlist, stats=stats)
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
