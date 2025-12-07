import { useRef, useCallback } from 'react'
import { GeoJSON } from 'react-leaflet'
import type { Layer, LeafletMouseEvent, PathOptions } from 'leaflet'
import type { Feature, Geometry } from 'geojson'
import type { FireRiskProperties, FireRiskCollection, FireRiskTier } from '@/types'
import { getHighlightStyle } from '@/lib/choroplethStyle'

interface FireRiskLayerProps {
  data: FireRiskCollection
  opacity: number
}

// Tier-based colors (categorical, not gradient)
export const FIRE_TIER_COLORS: Record<FireRiskTier, string> = {
  Low: '#22c55e', // green-500
  Moderate: '#eab308', // yellow-500
  High: '#f97316', // orange-500
  Extreme: '#dc2626', // red-600
}

// Tier labels for display
export const FIRE_TIER_LABELS: Record<FireRiskTier, string> = {
  Low: 'Low (0-39)',
  Moderate: 'Moderate (40-59)',
  High: 'High (60-79)',
  Extreme: 'Extreme (80-100)',
}

// Default color for unknown tiers
const FIRE_TIER_DEFAULT = '#d1d5db' // gray-300

export function FireRiskLayer({ data, opacity }: FireRiskLayerProps) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null)

  // Style function based on fire tier
  const styleFn = useCallback(
    (feature: Feature<Geometry, FireRiskProperties> | undefined): PathOptions => {
      if (!feature?.properties) {
        return { fillOpacity: 0, weight: 0 }
      }

      const tier = feature.properties.fire_tier as FireRiskTier
      const color = FIRE_TIER_COLORS[tier] || FIRE_TIER_DEFAULT

      return {
        fillColor: color,
        fillOpacity: 0.75 * opacity,
        color: '#374151',
        weight: 0.5,
        opacity: opacity,
      }
    },
    [opacity]
  )

  // Generate popup content
  const generatePopup = useCallback((props: FireRiskProperties): string => {
    const tierColor = FIRE_TIER_COLORS[props.fire_tier] || FIRE_TIER_DEFAULT

    return `
      <div class="p-2">
        <h3 class="font-bold text-sm mb-2">${props.APN}</h3>
        <div class="text-xs space-y-1">
          <div class="flex justify-between">
            <span class="text-gray-600">Fire Risk Score:</span>
            <span class="font-bold">${props.fire_risk?.toFixed(1) || 'N/A'}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">Risk Tier:</span>
            <span class="font-medium px-2 py-0.5 rounded text-white text-[10px]" style="background-color: ${tierColor}">${props.fire_tier}</span>
          </div>
          <hr class="my-1 border-gray-200" />
          <div class="flex justify-between">
            <span class="text-gray-600">In WUI:</span>
            <span class="font-medium">${props.in_wui === 1 ? 'Yes' : 'No'}</span>
          </div>
          ${
            props.wui_class
              ? `
          <div class="flex justify-between">
            <span class="text-gray-600">WUI Class:</span>
            <span class="font-medium">${props.wui_class}</span>
          </div>
          `
              : ''
          }
          ${
            props.fhsz_class
              ? `
          <div class="flex justify-between">
            <span class="text-gray-600">FHSZ Class:</span>
            <span class="font-medium">${props.fhsz_class}</span>
          </div>
          `
              : ''
          }
          <hr class="my-1 border-gray-200" />
          <div class="text-gray-500 text-[10px]">Nearest Historical Fire:</div>
          <div class="flex justify-between">
            <span class="text-gray-600">${props.nearest_fire_nm || 'Unknown'}:</span>
            <span class="font-medium">${props.nearest_fire_mi?.toFixed(1) || '?'} mi (${props.nearest_fire_yr || '?'})</span>
          </div>
          <hr class="my-1 border-gray-200" />
          <div class="text-gray-500 text-[10px]">Component Scores:</div>
          <div class="flex justify-between text-[10px]">
            <span>FHSZ (35%):</span>
            <span>${props.fr_fhsz?.toFixed(0) || 0}</span>
          </div>
          <div class="flex justify-between text-[10px]">
            <span>Slope (20%):</span>
            <span>${props.fr_slope?.toFixed(0) || 0}</span>
          </div>
          <div class="flex justify-between text-[10px]">
            <span>WUI (20%):</span>
            <span>${props.fr_wui?.toFixed(0) || 0}</span>
          </div>
          <div class="flex justify-between text-[10px]">
            <span>Historical (15%):</span>
            <span>${props.fr_hist?.toFixed(0) || 0}</span>
          </div>
          <div class="flex justify-between text-[10px]">
            <span>Vegetation (10%):</span>
            <span>${props.fr_veg?.toFixed(0) || 0}</span>
          </div>
        </div>
      </div>
    `
  }, [])

  // Event handlers for each feature
  const onEachFeature = useCallback(
    (feature: Feature<Geometry, FireRiskProperties>, layer: Layer) => {
      const pathLayer = layer as L.Path
      let originalStyle: PathOptions | null = null

      if (feature.properties) {
        pathLayer.bindPopup(generatePopup(feature.properties), {
          maxWidth: 320,
          className: 'custom-popup fire-risk-popup',
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

  // Key includes opacity to force re-render when changed
  const layerKey = `fire-risk-${opacity}`

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
