import { useRef, useCallback } from 'react'
import { GeoJSON } from 'react-leaflet'
import type { Layer, LeafletMouseEvent, PathOptions } from 'leaflet'
import type { Feature, FeatureCollection, Geometry } from 'geojson'
import type { LayerConfig } from '@/types'
import {
  createChoroplethStyleFn,
  createStaticStyle,
  getHighlightStyle,
} from '@/lib/choroplethStyle'
import { generatePopupContent } from '@/lib/popupContent'

interface GeoJSONLayerProps {
  config: LayerConfig
  data: FeatureCollection
  opacity: number
}

export function GeoJSONLayer({ config, data, opacity }: GeoJSONLayerProps) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null)

  // Create style function based on config
  const styleFn = useCallback(
    (feature: Feature<Geometry, Record<string, unknown>> | undefined): PathOptions => {
      if (!feature) {
        return createStaticStyle(config.style, opacity)
      }

      if (config.choropleth) {
        const choroplethStyle = createChoroplethStyleFn(config.choropleth, opacity)
        return choroplethStyle(feature.properties ?? {})
      }

      return createStaticStyle(config.style, opacity)
    },
    [config, opacity]
  )

  // Event handlers for each feature
  const onEachFeature = useCallback(
    (feature: Feature<Geometry, Record<string, unknown>>, layer: Layer) => {
      // Store original style for reset
      const pathLayer = layer as L.Path
      let originalStyle: PathOptions | null = null

      // Bind popup if configured
      if (config.popup) {
        const content = generatePopupContent(config.popup, feature.properties ?? {})
        pathLayer.bindPopup(content, {
          maxWidth: 300,
          className: 'custom-popup',
        })
      }

      // Hover highlighting
      pathLayer.on({
        mouseover: (e: LeafletMouseEvent) => {
          const target = e.target as L.Path
          originalStyle = {
            weight: (target.options as PathOptions).weight,
            color: (target.options as PathOptions).color,
            fillOpacity: (target.options as PathOptions).fillOpacity,
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
    [config.popup]
  )

  return (
    <GeoJSON
      ref={geoJsonRef}
      key={`${config.id}-${opacity}`}
      data={data}
      style={styleFn}
      onEachFeature={onEachFeature}
    />
  )
}
