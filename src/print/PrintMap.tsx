import { useEffect, useRef } from 'react'
import maplibregl, { Map as MapLibreMap } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { pt } from './printConfig'

interface PrintMapProps {
  boundaryUrl: string
  bbox: [number, number, number, number]
  styleUrl?: string
  onReady?: (map: MapLibreMap) => void
}

const DEFAULT_STYLE = 'https://tiles.openfreemap.org/styles/positron'

const BOUNDARY_SOURCE = 'district-boundary'
const MASK_SOURCE = 'world-mask'
const BOUNDARY_CASING_LAYER = 'district-boundary-casing'
const BOUNDARY_LINE_LAYER = 'district-boundary-line'
const MASK_LAYER = 'world-mask-fill'

// Boundary stroke — sized in points so it stays at the same physical width
// regardless of render DPI.
const BOUNDARY_LINE_WIDTH = pt(5) // ~0.07" on final poster
const BOUNDARY_LINE_COLOR = '#b91c1c'
const BOUNDARY_CASING_WIDTH = pt(10) // ~0.14" on final poster
const BOUNDARY_CASING_COLOR = '#ffffff'

// Mask: dim outside areas to push focus into the district while keeping enough
// signal that residents can orient against neighboring streets.
const MASK_FILL = '#ffffff'
const MASK_OPACITY = 0.65

const WORLD_RING: [number, number][] = [
  [-180, -85],
  [180, -85],
  [180, 85],
  [-180, 85],
  [-180, -85],
]

// Road style overrides — darker, thicker than positron's defaults. Widths are
// in points so they stay constant at any render resolution.
const ROAD_OVERRIDES: Array<{
  test: (id: string) => boolean
  color: string
  width: number
}> = [
  { test: (id) => id === 'road_motorway', color: '#d97706', width: pt(3) },
  { test: (id) => id === 'road_motorway_casing', color: '#b45309', width: pt(4) },
  { test: (id) => id === 'road_trunk_primary', color: '#404040', width: pt(2.5) },
  { test: (id) => id === 'road_trunk_primary_casing', color: '#1f2937', width: pt(3.2) },
  { test: (id) => id === 'road_secondary_tertiary', color: '#525252', width: pt(2) },
  { test: (id) => id === 'road_secondary_tertiary_casing', color: '#262626', width: pt(2.7) },
  { test: (id) => id === 'road_minor', color: '#737373', width: pt(1.4) },
  { test: (id) => id === 'road_minor_casing', color: '#525252', width: pt(1.8) },
  { test: (id) => id === 'road_path', color: '#a3a3a3', width: pt(0.8) },
]

// Label sizes in points — what they will measure on the printed poster.
// `minzoom` is optional; when set we override the positron default so labels
// render at our current zoom even if they would normally be hidden.
const LABEL_OVERRIDES: Array<{
  test: (id: string) => boolean
  textSize: number
  haloWidth: number
  color: string
  halo: string
  minzoom?: number
}> = [
  // Major road labels — arterials, highway names.
  {
    test: (id) => id === 'highway-name-major',
    textSize: pt(14),
    haloWidth: pt(1.5),
    color: '#1f2937',
    halo: '#ffffff',
  },
  // Residential street names — the critical layer for "find your street".
  // Positron hides these below z15; we render at ~z14.8, so we lower it.
  {
    test: (id) => id === 'highway-name-minor',
    textSize: pt(9),
    haloWidth: pt(1.2),
    color: '#374151',
    halo: '#ffffff',
    minzoom: 13,
  },
  // Paths / trails — keep hidden to reduce label clutter.
  {
    test: (id) => id === 'highway-name-path',
    textSize: pt(7),
    haloWidth: pt(1),
    color: '#4b5563',
    halo: '#ffffff',
    minzoom: 14,
  },
  // Route shields (32, 99, I-5, etc.)
  {
    test: (id) => /shield/.test(id),
    textSize: pt(10),
    haloWidth: pt(1.2),
    color: '#111827',
    halo: '#ffffff',
  },
  // Suburb / neighborhood labels — strong presence for orientation.
  {
    test: (id) => id === 'label_other',
    textSize: pt(20),
    haloWidth: pt(2.5),
    color: '#111827',
    halo: '#ffffff',
  },
  // Village / town labels.
  {
    test: (id) => id === 'label_village' || id === 'label_town',
    textSize: pt(18),
    haloWidth: pt(2.2),
    color: '#1f2937',
    halo: '#ffffff',
  },
  // Water names.
  {
    test: (id) => /water_name/.test(id) || id === 'waterway_line_label',
    textSize: pt(10),
    haloWidth: pt(1.2),
    color: '#1e40af',
    halo: '#ffffff',
  },
]

function buildMaskFeature(boundary: GeoJSON.FeatureCollection): GeoJSON.Feature {
  const holes: [number, number][][] = []
  for (const feat of boundary.features) {
    const g = feat.geometry
    if (g.type === 'Polygon') {
      for (const ring of g.coordinates) holes.push(ring as [number, number][])
    } else if (g.type === 'MultiPolygon') {
      for (const poly of g.coordinates) {
        for (const ring of poly) holes.push(ring as [number, number][])
      }
    }
  }
  return {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'Polygon',
      coordinates: [WORLD_RING, ...holes],
    },
  }
}

function applyRoadOverrides(map: MapLibreMap) {
  const style = map.getStyle()
  for (const layer of style.layers ?? []) {
    if (layer.type !== 'line') continue
    for (const override of ROAD_OVERRIDES) {
      if (override.test(layer.id)) {
        try {
          map.setPaintProperty(layer.id, 'line-color', override.color)
          map.setPaintProperty(layer.id, 'line-width', override.width)
          map.setPaintProperty(layer.id, 'line-opacity', 1.0)
        } catch {
          /* ignore */
        }
        break
      }
    }
  }
}

function applyLabelOverrides(map: MapLibreMap) {
  const style = map.getStyle()
  for (const layer of style.layers ?? []) {
    if (layer.type !== 'symbol') continue
    for (const override of LABEL_OVERRIDES) {
      if (override.test(layer.id)) {
        try {
          map.setLayoutProperty(layer.id, 'text-size', override.textSize)
          map.setPaintProperty(layer.id, 'text-color', override.color)
          map.setPaintProperty(layer.id, 'text-halo-color', override.halo)
          map.setPaintProperty(layer.id, 'text-halo-width', override.haloWidth)
          if (override.minzoom !== undefined) {
            map.setLayerZoomRange(layer.id, override.minzoom, 24)
          }
        } catch {
          /* ignore */
        }
        break
      }
    }
  }
}

export function PrintMap({ boundaryUrl, bbox, styleUrl = DEFAULT_STYLE, onReady }: PrintMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      bounds: bbox,
      fitBoundsOptions: { padding: pt(20), animate: false },
      interactive: false,
      attributionControl: false,
      canvasContextAttributes: { preserveDrawingBuffer: true },
    })
    mapRef.current = map
    ;(window as unknown as { __printMap?: MapLibreMap }).__printMap = map

    map.on('load', async () => {
      const resp = await fetch(boundaryUrl)
      const boundary = (await resp.json()) as GeoJSON.FeatureCollection

      applyRoadOverrides(map)
      applyLabelOverrides(map)

      const labelLayers = map.getStyle().layers ?? []
      const firstSymbolId = labelLayers.find((l) => l.type === 'symbol')?.id

      map.addSource(MASK_SOURCE, {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [buildMaskFeature(boundary)],
        },
      })
      map.addLayer(
        {
          id: MASK_LAYER,
          type: 'fill',
          source: MASK_SOURCE,
          paint: {
            'fill-color': MASK_FILL,
            'fill-opacity': MASK_OPACITY,
            'fill-antialias': true,
          },
        },
        firstSymbolId,
      )

      map.addSource(BOUNDARY_SOURCE, { type: 'geojson', data: boundary })
      map.addLayer({
        id: BOUNDARY_CASING_LAYER,
        type: 'line',
        source: BOUNDARY_SOURCE,
        paint: {
          'line-color': BOUNDARY_CASING_COLOR,
          'line-width': BOUNDARY_CASING_WIDTH,
          'line-opacity': 1,
        },
        layout: { 'line-join': 'round', 'line-cap': 'round' },
      })
      map.addLayer({
        id: BOUNDARY_LINE_LAYER,
        type: 'line',
        source: BOUNDARY_SOURCE,
        paint: {
          'line-color': BOUNDARY_LINE_COLOR,
          'line-width': BOUNDARY_LINE_WIDTH,
          'line-opacity': 1,
        },
        layout: { 'line-join': 'round', 'line-cap': 'round' },
      })

      onReady?.(map)
    })

    return () => {
      map.remove()
      mapRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [styleUrl])

  return <div ref={containerRef} className="h-full w-full" />
}
