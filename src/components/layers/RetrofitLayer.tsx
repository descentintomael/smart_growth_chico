import { useRef, useCallback, useMemo } from 'react'
import { GeoJSON } from 'react-leaflet'
import chroma from 'chroma-js'
import type { Layer, LeafletMouseEvent, PathOptions } from 'leaflet'
import type { Feature, Geometry, FeatureCollection } from 'geojson'
import type {
  RetrofitLayerId,
  ParkingRetrofitProperties,
  VacantInfillProperties,
  CommercialRetrofitProperties,
} from '@/types'
import { useRetrofitStore } from '@/stores/retrofitStore'
import { generatePopupContent } from '@/lib/popupContent'
import { getLayerConfig } from '@/data/layerConfig'
import { getHighlightStyle } from '@/lib/choroplethStyle'

interface RetrofitLayerProps {
  layerId: RetrofitLayerId
  data: FeatureCollection<
    Geometry,
    ParkingRetrofitProperties | VacantInfillProperties | CommercialRetrofitProperties
  >
  opacity: number
}

// Color scale for potential housing units (YlOrRd - yellow to red)
export const RETROFIT_COLOR_SCALE = [
  '#ffffcc',
  '#ffeda0',
  '#fed976',
  '#feb24c',
  '#fd8d3c',
  '#fc4e2a',
  '#e31a1c',
  '#bd0026',
  '#800026',
]

// Max units per layer type (used for color scale domain)
const MAX_UNITS: Record<RetrofitLayerId, number> = {
  'parking-retrofit': 400,
  'vacant-infill': 1300,
  'commercial-retrofit': 450,
}

export function RetrofitLayer({ layerId, data, opacity }: RetrofitLayerProps) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null)

  // Get adoption percentage for layers that support it
  const vacantAdoption = useRetrofitStore((state) => state.vacantAdoption)
  const commercialAdoption = useRetrofitStore((state) => state.commercialAdoption)

  // Determine adoption percentage for current layer
  const adoptionPercent = useMemo(() => {
    if (layerId === 'vacant-infill') return vacantAdoption
    if (layerId === 'commercial-retrofit') return commercialAdoption
    return 100 // parking-retrofit has no adoption slider
  }, [layerId, vacantAdoption, commercialAdoption])

  // Color scale for potential units
  const colorScale = useMemo(() => {
    const maxUnits = MAX_UNITS[layerId]
    return chroma.scale(RETROFIT_COLOR_SCALE).domain([0, maxUnits]).mode('lab')
  }, [layerId])

  // Calculate the effective units based on adoption percentage
  const getEffectiveUnits = useCallback(
    (potUnits: number): number => {
      // For parking-retrofit, always show full potential
      if (layerId === 'parking-retrofit') return potUnits
      // For others, scale by adoption percentage
      return Math.round(potUnits * (adoptionPercent / 100))
    },
    [layerId, adoptionPercent]
  )

  // Style function for features
  const styleFn = useCallback(
    (
      feature:
        | Feature<
            Geometry,
            ParkingRetrofitProperties | VacantInfillProperties | CommercialRetrofitProperties
          >
        | undefined
    ): PathOptions => {
      if (!feature?.properties) {
        return { fillOpacity: 0, weight: 0 }
      }

      const props = feature.properties
      const effectiveUnits = getEffectiveUnits(props.pot_units)

      return {
        fillColor: colorScale(effectiveUnits).hex(),
        fillOpacity: 0.7 * opacity,
        color: '#374151', // gray-700
        weight: 1,
        opacity: opacity,
      }
    },
    [colorScale, getEffectiveUnits, opacity]
  )

  // Get popup config from layer config
  const config = getLayerConfig(layerId)

  // Event handlers for each feature
  const onEachFeature = useCallback(
    (
      feature: Feature<
        Geometry,
        ParkingRetrofitProperties | VacantInfillProperties | CommercialRetrofitProperties
      >,
      layer: Layer
    ) => {
      const pathLayer = layer as L.Path
      let originalStyle: PathOptions | null = null

      if (config?.popup && feature.properties) {
        const content = generatePopupContent(
          config.popup,
          feature.properties as unknown as Record<string, unknown>
        )
        pathLayer.bindPopup(content, {
          maxWidth: 320,
          className: 'custom-popup retrofit-popup',
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

  // Key includes layer ID and adoption percent to force re-render when changed
  const layerKey = `${layerId}-${adoptionPercent}-${opacity}`

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
