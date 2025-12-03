import { useRef, useCallback, useMemo } from 'react'
import { GeoJSON } from 'react-leaflet'
import chroma from 'chroma-js'
import type { Layer, LeafletMouseEvent, PathOptions } from 'leaflet'
import type { Feature, Geometry } from 'geojson'
import type { CommercialViabilitySiteProperties, CommercialViabilitySiteCollection } from '@/types'
import { useCommercialViabilityStore } from '@/stores/commercialViabilityStore'
import { generatePopupContent } from '@/lib/popupContent'
import { getLayerConfig } from '@/data/layerConfig'
import { getHighlightStyle } from '@/lib/choroplethStyle'

interface CommercialViabilityLayerProps {
  data: CommercialViabilitySiteCollection
  opacity: number
}

// Color scale for viable businesses (0-8 range, sequential green)
export const COMMERCIAL_VIABILITY_SCALE = [
  '#f7fcf5',
  '#e5f5e0',
  '#c7e9c0',
  '#a1d99b',
  '#74c476',
  '#41ab5d',
  '#238b45',
  '#006d2c',
  '#00441b',
]
export const COMMERCIAL_VIABILITY_DOMAIN: [number, number] = [0, 8]

export function CommercialViabilityLayer({ data, opacity }: CommercialViabilityLayerProps) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null)

  const adoptionPercent = useCommercialViabilityStore((state) => state.adoptionPercent)
  const summary = useCommercialViabilityStore((state) => state.summary)

  // Get the viable business count for a site at the current adoption rate
  const getSiteViableCount = useCallback(
    (siteName: string, currentCount: number): number => {
      if (!summary || adoptionPercent === 0) {
        return currentCount
      }

      // Find the site in summary data
      const site = summary.opportunity_sites.find((s) => s.name === siteName)
      if (!site) {
        return currentCount
      }

      // Get the nearest breakpoint (25, 50, 75, 100)
      const breakpoints = [25, 50, 75, 100]
      let nearestBreakpoint = 25

      if (adoptionPercent <= 0) {
        return site.businesses_current_count
      }

      for (const bp of breakpoints) {
        if (adoptionPercent <= bp) {
          nearestBreakpoint = bp
          break
        }
        nearestBreakpoint = bp
      }

      const scenario = site.adoption_scenarios[nearestBreakpoint.toString()]
      return scenario?.businesses_viable_count ?? currentCount
    },
    [summary, adoptionPercent]
  )

  // Color scale for viable businesses
  const viabilityColorScale = useMemo(() => {
    return chroma.scale(COMMERCIAL_VIABILITY_SCALE).domain(COMMERCIAL_VIABILITY_DOMAIN).mode('lab')
  }, [])

  // Style function for sites
  const styleFn = useCallback(
    (feature: Feature<Geometry, CommercialViabilitySiteProperties> | undefined): PathOptions => {
      if (!feature?.properties) {
        return { fillOpacity: 0, weight: 0 }
      }

      const props = feature.properties
      const viableCount = getSiteViableCount(props.site_name, props.cur_biz_cnt)

      return {
        fillColor: viabilityColorScale(viableCount).hex(),
        fillOpacity: 0.7 * opacity,
        color: '#374151', // gray-700
        weight: 2,
        opacity: opacity,
      }
    },
    [getSiteViableCount, viabilityColorScale, opacity]
  )

  // Get popup config from layer config
  const config = getLayerConfig('commercial-viability')

  // Event handlers for each feature
  const onEachFeature = useCallback(
    (feature: Feature<Geometry, CommercialViabilitySiteProperties>, layer: Layer) => {
      const pathLayer = layer as L.Path
      let originalStyle: PathOptions | null = null

      if (config?.popup && feature.properties) {
        const content = generatePopupContent(
          config.popup,
          feature.properties as unknown as Record<string, unknown>
        )
        pathLayer.bindPopup(content, {
          maxWidth: 320,
          className: 'custom-popup commercial-popup',
        })
      }

      // Hover highlighting
      pathLayer.on({
        mouseover: (e: LeafletMouseEvent) => {
          const target = e.target as L.Path
          originalStyle = {
            weight: target.options.weight,
            color: target.options.color,
            fillOpacity: target.options.fillOpacity,
          }
          target.setStyle(getHighlightStyle())
          target.bringToFront()
        },
        mouseout: (e: LeafletMouseEvent) => {
          const target = e.target as L.Path
          if (originalStyle) {
            target.setStyle(originalStyle)
          }
        },
      })
    },
    [config]
  )

  // Key includes adoption percent to force re-render when changed
  const layerKey = `commercial-viability-${adoptionPercent}-${opacity}`

  return (
    <GeoJSON
      ref={geoJsonRef}
      key={layerKey}
      data={data}
      style={styleFn as (feature: Feature<Geometry, unknown> | undefined) => PathOptions}
      onEachFeature={
        onEachFeature as (feature: Feature<Geometry, unknown>, layer: Layer) => void
      }
    />
  )
}
