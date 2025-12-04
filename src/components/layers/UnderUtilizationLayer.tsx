import { useRef, useCallback, useMemo } from 'react'
import { GeoJSON } from 'react-leaflet'
import chroma from 'chroma-js'
import type { Layer, LeafletMouseEvent, PathOptions } from 'leaflet'
import type { Feature, Geometry } from 'geojson'
import type {
  UnderUtilizationProperties,
  UnderUtilizationCollection,
  UnderUtilizationMetric,
} from '@/types'
import { useUnderUtilizationStore } from '@/stores/underUtilizationStore'
import { getHighlightStyle } from '@/lib/choroplethStyle'

interface UnderUtilizationLayerProps {
  data: UnderUtilizationCollection
  opacity: number
}

// Color scale for under-utilization (0-100)
// Yellow to red: higher = more underutilized = more urgent
const UU_COLOR_SCALE = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']
const UU_DOMAIN: [number, number] = [0, 100]

// Metric labels for display
const METRIC_LABELS: Record<UnderUtilizationMetric, string> = {
  composite: 'Composite Score',
  vertical: 'Vertical (FAR)',
  improvement: 'Improvement Ratio',
  density: 'Density Headroom',
  upzone: 'Upzone Potential',
}

// Property names for each metric
const METRIC_PROPERTY: Record<UnderUtilizationMetric, keyof UnderUtilizationProperties> = {
  composite: 'uu_composite',
  vertical: 'uu_vertical',
  improvement: 'uu_improvement',
  density: 'uu_density',
  upzone: 'uu_upzone',
}

// Tier property names for each metric
const TIER_PROPERTY: Record<UnderUtilizationMetric, keyof UnderUtilizationProperties> = {
  composite: 'tier_comp',
  vertical: 'tier_vert',
  improvement: 'tier_imp',
  density: 'tier_dens',
  upzone: 'tier_upz',
}

export function UnderUtilizationLayer({ data, opacity }: UnderUtilizationLayerProps) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null)

  const selectedMetric = useUnderUtilizationStore((state) => state.selectedMetric)

  // Color scale for under-utilization
  const colorScale = useMemo(() => {
    return chroma.scale(UU_COLOR_SCALE).domain(UU_DOMAIN).mode('lab')
  }, [])

  // Style function based on selected metric
  const styleFn = useCallback(
    (feature: Feature<Geometry, UnderUtilizationProperties> | undefined): PathOptions => {
      if (!feature?.properties) {
        return { fillOpacity: 0, weight: 0 }
      }

      const props = feature.properties
      const property = METRIC_PROPERTY[selectedMetric]
      const value = props[property] as number

      // Handle null/undefined values
      if (value === null || value === undefined || isNaN(value)) {
        return {
          fillOpacity: 0,
          weight: 0.5,
          color: '#d1d5db',
          opacity: 0.2 * opacity,
        }
      }

      return {
        fillColor: colorScale(value).hex(),
        fillOpacity: 0.75 * opacity,
        color: '#374151',
        weight: 0.5,
        opacity: opacity,
      }
    },
    [selectedMetric, colorScale, opacity]
  )

  // Generate popup content
  const generatePopup = useCallback(
    (props: UnderUtilizationProperties): string => {
      const metricValue = props[METRIC_PROPERTY[selectedMetric]] as number
      const tierValue = props[TIER_PROPERTY[selectedMetric]] as string

      const formatNumber = (n: number | null | undefined): string => {
        if (n === null || n === undefined || isNaN(n)) return 'N/A'
        return n.toFixed(1)
      }

      return `
        <div class="p-2">
          <h3 class="font-bold text-sm mb-2">${props.APN}</h3>
          <div class="text-xs space-y-1">
            <div class="flex justify-between">
              <span class="text-gray-600">Zone:</span>
              <span class="font-medium">${props.zoning || 'N/A'}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Acres:</span>
              <span class="font-medium">${props.Lt_Acre?.toFixed(2) || 'N/A'}</span>
            </div>
            <hr class="my-1 border-gray-200" />
            <div class="flex justify-between">
              <span class="text-gray-600">${METRIC_LABELS[selectedMetric]}:</span>
              <span class="font-bold">${formatNumber(metricValue)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Tier:</span>
              <span class="font-medium ${tierValue === 'Severe' ? 'text-red-600' : tierValue === 'High' ? 'text-orange-600' : ''}">${tierValue}</span>
            </div>
            <hr class="my-1 border-gray-200" />
            <div class="text-gray-500 text-[10px]">All Metrics:</div>
            <div class="flex justify-between text-[10px]">
              <span>Composite:</span>
              <span>${formatNumber(props.uu_composite)}</span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span>Vertical:</span>
              <span>${formatNumber(props.uu_vertical)}</span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span>Improvement:</span>
              <span>${formatNumber(props.uu_improvement)}</span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span>Density:</span>
              <span>${formatNumber(props.uu_density)}</span>
            </div>
            <div class="flex justify-between text-[10px]">
              <span>Upzone:</span>
              <span>${formatNumber(props.uu_upzone)}</span>
            </div>
            ${
              props.foregone_units > 0
                ? `
            <hr class="my-1 border-gray-200" />
            <div class="flex justify-between">
              <span class="text-gray-600">Foregone Units:</span>
              <span class="font-medium">${props.foregone_units}</span>
            </div>
            `
                : ''
            }
          </div>
        </div>
      `
    },
    [selectedMetric]
  )

  // Event handlers for each feature
  const onEachFeature = useCallback(
    (feature: Feature<Geometry, UnderUtilizationProperties>, layer: Layer) => {
      const pathLayer = layer as L.Path
      let originalStyle: PathOptions | null = null

      if (feature.properties) {
        pathLayer.bindPopup(generatePopup(feature.properties), {
          maxWidth: 320,
          className: 'custom-popup under-utilization-popup',
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
    [generatePopup]
  )

  // Key includes metric to force re-render when changed
  const layerKey = `under-utilization-${selectedMetric}-${opacity}`

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

// Export constants for use in legend
export { UU_COLOR_SCALE, UU_DOMAIN, METRIC_LABELS }
