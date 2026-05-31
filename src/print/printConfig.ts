/**
 * Print canvas configuration. All sizes are computed from the render dimensions
 * so the same component scales cleanly from preview → 36"×48" poster export.
 */

// Final poster size in inches.
export const POSTER_INCHES_WIDTH = 36
export const POSTER_INCHES_HEIGHT = 48

// Logical render dimensions in CSS pixels.
//
// At 200 DPI we render the full 36×48" poster as 7200×9600 pixels. This lands
// the fit-to-district zoom at ~z15.6 — high enough that even short residential
// street segments have enough on-screen length for MapLibre to place a label
// without collision.
//
// 200 DPI is a comfortable print resolution for a poster viewed at a few feet.
export const PRINT_WIDTH = 7200
export const PRINT_HEIGHT = 9600

// Effective DPI of the current render.
export const PREVIEW_DPI = PRINT_WIDTH / POSTER_INCHES_WIDTH // 150

// Convert points → render pixels. 1pt = 1/72 inch.
export const pt = (points: number) => (points / 72) * PREVIEW_DPI

// On-screen scale factor. The print canvas is far too large to view 1:1, so we
// scale it down with a CSS transform for browser viewing. The screenshot script
// strips this transform before capture.
export const SCREEN_SCALE = 0.12

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
