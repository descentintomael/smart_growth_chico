/**
 * Print canvas configuration. All sizes are computed from the render dimensions
 * so the same component scales cleanly from preview → 36"×48" poster export.
 */

// Final poster size in inches.
export const POSTER_INCHES_WIDTH = 36
export const POSTER_INCHES_HEIGHT = 48

// Logical render dimensions in CSS pixels.
//
// At 150 DPI we render the full 36×48" poster as 5400×7200 pixels. The
// MapLibre fit-bounds at that size lands the district at ~z16, which is the
// minzoom for positron's `highway-name-minor` layer — so individual residential
// street names become visible.
//
// 150 DPI is a reasonable print resolution for posters viewed at a few feet.
// For an even sharper export we can bump these dimensions later; the code is
// resolution-agnostic.
export const PRINT_WIDTH = 5400
export const PRINT_HEIGHT = 7200

// Effective DPI of the current render.
export const PREVIEW_DPI = PRINT_WIDTH / POSTER_INCHES_WIDTH // 150

// Convert points → render pixels. 1pt = 1/72 inch.
export const pt = (points: number) => (points / 72) * PREVIEW_DPI

// On-screen scale factor. The print canvas is far too large to view 1:1, so we
// scale it down with a CSS transform for browser viewing. The screenshot script
// strips this transform before capture.
export const SCREEN_SCALE = 0.16

// District 6 bounding box (lon/lat) — derived from district-boundary.geojson.
export const DISTRICT_6_BBOX: [number, number, number, number] = [
  -121.84387, 39.69973, -121.71237, 39.81408,
]

// Layout — header/footer heights, in points for resolution independence.
export const HEADER_HEIGHT = pt(220) // 3.06" of header on a 48" poster
export const FOOTER_HEIGHT = pt(80) // 1.11" of footer
export const PAGE_PADDING = pt(48) // 0.67" page margin

// Type scale (point sizes on the final poster).
export const TITLE_PT = 72
export const SUBTITLE_PT = 26
export const FOOTER_PT = 12
