import { useRef, useCallback, useMemo } from 'react'
import { GeoJSON } from 'react-leaflet'
import chroma from 'chroma-js'
import type { Layer, LeafletMouseEvent, PathOptions } from 'leaflet'
import type { Feature, Geometry } from 'geojson'
import type { UpzoneParcelProperties, UpzoneCollection } from '@/types'
import { useUpzoneStore } from '@/stores/upzoneStore'
import { generatePopupContent } from '@/lib/popupContent'
import { getLayerConfig } from '@/data/layerConfig'
import { getHighlightStyle } from '@/lib/choroplethStyle'

interface UpzoneScenarioLayerProps {
  data: UpzoneCollection
  opacity: number
}

// Color scale for delta_sg_index (green gradient for positive values)
const DELTA_SG_SCALE = ['#f7f7f7', '#a6dba0', '#5aae61', '#1b7837']
const DELTA_SG_DOMAIN: [number, number] = [0, 20]

export function UpzoneScenarioLayer({ data, opacity }: UpzoneScenarioLayerProps) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null)

  const adoptionPercent = useUpzoneStore((state) => state.adoptionPercent)
  const viewMode = useUpzoneStore((state) => state.viewMode)

  // Compute which parcels are "adopted" based on priority ranking
  // The data is pre-sorted by adoption_priority (lowest first = highest priority)
  const adoptedAPNs = useMemo(() => {
    // Get all eligible parcels (they're already sorted by priority in the data)
    const eligibleParcels = data.features.filter(
      (f) => f.properties?.upzone_elig === 1 && f.properties?.adoption_priority !== null
    )

    const totalEligible = eligibleParcels.length
    const targetCount = Math.round((adoptionPercent / 100) * totalEligible)

    // Take the first N parcels (highest priority = lowest adoption_priority value)
    const adopted = new Set<string>()
    for (let i = 0; i < targetCount && i < eligibleParcels.length; i++) {
      const apn = eligibleParcels[i]?.properties?.APN
      if (apn) {
        adopted.add(apn)
      }
    }

    return adopted
  }, [data, adoptionPercent])

  // Color scale for delta SG index
  const deltaColorScale = useMemo(() => {
    return chroma.scale(DELTA_SG_SCALE).domain(DELTA_SG_DOMAIN).mode('lab')
  }, [])

  // Style function based on adoption state
  const styleFn = useCallback(
    (feature: Feature<Geometry, UpzoneParcelProperties> | undefined): PathOptions => {
      if (!feature?.properties) {
        return { fillOpacity: 0, weight: 0 }
      }

      const props = feature.properties
      const isEligible = props.upzone_elig === 1
      const isAdopted = adoptedAPNs.has(props.APN)

      // Non-eligible parcels: very faint or hidden
      if (!isEligible) {
        return {
          fillOpacity: 0,
          weight: 0.5,
          color: '#d1d5db', // gray-300
          opacity: 0.2 * opacity,
        }
      }

      // Eligible but not adopted: dashed outline only, no fill
      if (!isAdopted) {
        return {
          fillOpacity: 0,
          weight: 1,
          color: '#6b7280', // gray-500
          opacity: 0.5 * opacity,
          dashArray: '4,4',
        }
      }

      // Adopted parcels: choropleth fill based on delta_sg_index or current value
      let colorValue: number
      if (viewMode === 'projected') {
        // Show delta (change in SG index)
        colorValue = Math.max(0, props.delta_sg_index)
      } else {
        // Show current SG index (normalized to 0-20 range for comparison)
        colorValue = (props.cur_sg_index / 100) * 20
      }

      return {
        fillColor: deltaColorScale(colorValue).hex(),
        fillOpacity: 0.7 * opacity,
        color: '#374151', // gray-700
        weight: 1,
        opacity: opacity,
      }
    },
    [adoptedAPNs, deltaColorScale, opacity, viewMode]
  )

  // Get popup config from layer config
  const config = getLayerConfig('upzone-scenario')

  // Event handlers for each feature
  const onEachFeature = useCallback(
    (feature: Feature<Geometry, UpzoneParcelProperties>, layer: Layer) => {
      const pathLayer = layer as L.Path
      let originalStyle: PathOptions | null = null

      // Only show popup for eligible parcels (or all parcels if you want)
      if (config?.popup && feature.properties) {
        const content = generatePopupContent(
          config.popup,
          feature.properties as unknown as Record<string, unknown>
        )
        pathLayer.bindPopup(content, {
          maxWidth: 320,
          className: 'custom-popup upzone-popup',
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
            dashArray: target.options.dashArray,
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

  // Key includes adoption percent and view mode to force re-render when changed
  const layerKey = `upzone-scenario-${adoptionPercent}-${viewMode}-${opacity}`

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

// Export color scale constants for use in legend
export { DELTA_SG_SCALE, DELTA_SG_DOMAIN }
