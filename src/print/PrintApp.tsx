import { useRef, useState } from 'react'
import type { Map as MapLibreMap } from 'maplibre-gl'
import { PrintMap } from './PrintMap'
import {
  DISTRICT_6_BBOX,
  FOOTER_HEIGHT,
  FOOTER_PT,
  HEADER_HEIGHT,
  PAGE_PADDING,
  PRINT_HEIGHT,
  PRINT_WIDTH,
  pt,
  SCREEN_SCALE,
  SUBTITLE_PT,
  TITLE_PT,
} from './printConfig'

export function PrintApp() {
  const mapRef = useRef<MapLibreMap | null>(null)
  const [exporting, setExporting] = useState(false)

  const handleExportPng = async () => {
    const map = mapRef.current
    if (!map) return
    setExporting(true)
    try {
      await new Promise<void>((resolve) => {
        if (map.areTilesLoaded() && !map.isMoving()) {
          resolve()
          return
        }
        const onIdle = () => {
          map.off('idle', onIdle)
          resolve()
        }
        map.on('idle', onIdle)
      })
      // Wait one more frame to be safe at high res.
      await new Promise((r) => requestAnimationFrame(() => r(null)))
      const dataUrl = map.getCanvas().toDataURL('image/png')
      const a = document.createElement('a')
      a.href = dataUrl
      a.download = `district-6-map-${PRINT_WIDTH}x${PRINT_HEIGHT}.png`
      a.click()
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="min-h-screen bg-neutral-200 py-6">
      <div className="mx-auto flex flex-col items-center gap-4">
        {/* Toolbar — not part of the printed canvas */}
        <div className="flex items-center gap-3 rounded-md bg-white px-4 py-2 shadow-sm">
          <span className="text-sm text-neutral-600">
            Preview {PRINT_WIDTH}×{PRINT_HEIGHT}px @ {(SCREEN_SCALE * 100).toFixed(0)}% ·
            scales to 36"×48" poster
          </span>
          <button
            onClick={handleExportPng}
            disabled={exporting}
            className="rounded bg-neutral-900 px-3 py-1 text-sm font-medium text-white hover:bg-neutral-700 disabled:opacity-60"
          >
            {exporting ? 'Exporting…' : 'Export map PNG'}
          </button>
        </div>

        {/* Screen-only scale wrapper. The export script removes this transform
            so the screenshot captures the canvas at its true print dimensions. */}
        <div
          id="print-scale-wrapper"
          style={{
            transform: `scale(${SCREEN_SCALE})`,
            transformOrigin: 'top left',
            width: PRINT_WIDTH * SCREEN_SCALE,
            height: PRINT_HEIGHT * SCREEN_SCALE,
          }}
        >
          <div
            id="print-canvas"
            className="relative flex flex-col bg-white shadow-xl ring-1 ring-neutral-300"
            style={{ width: PRINT_WIDTH, height: PRINT_HEIGHT }}
          >
            <header
              className="flex flex-col justify-end"
              style={{
                height: HEADER_HEIGHT,
                paddingLeft: PAGE_PADDING,
                paddingRight: PAGE_PADDING,
                paddingBottom: pt(18),
                borderBottom: `${pt(0.75)}px solid #d4d4d4`,
              }}
            >
              <h1
                style={{
                  fontSize: pt(TITLE_PT),
                  lineHeight: 1.05,
                  fontWeight: 600,
                  letterSpacing: '-0.02em',
                  color: '#0f172a',
                  margin: 0,
                }}
              >
                Chico City Council District 6
              </h1>
              <p
                style={{
                  fontSize: pt(SUBTITLE_PT),
                  marginTop: pt(6),
                  color: '#525252',
                  margin: 0,
                  marginBlockStart: pt(6),
                }}
              >
                Streets & District Boundary
              </p>
            </header>

            <div className="relative flex-1 overflow-hidden">
              <PrintMap
                boundaryUrl="/data/candidate-district-6/district-boundary.geojson"
                bbox={DISTRICT_6_BBOX}
                onReady={(m) => {
                  mapRef.current = m
                }}
              />
            </div>

            <footer
              className="flex items-center justify-between"
              style={{
                height: FOOTER_HEIGHT,
                paddingLeft: PAGE_PADDING,
                paddingRight: PAGE_PADDING,
                borderTop: `${pt(0.75)}px solid #d4d4d4`,
                fontSize: pt(FOOTER_PT),
                color: '#6b7280',
              }}
            >
              <span>Data: OpenStreetMap contributors · City of Chico</span>
              <span>Generated {new Date().toISOString().slice(0, 10)}</span>
            </footer>
          </div>
        </div>
      </div>
    </div>
  )
}
