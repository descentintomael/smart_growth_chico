import chroma from 'chroma-js'
import type { PathOptions } from 'leaflet'
import type { ChoroplethConfig, LayerStyle } from '@/types'

/**
 * Create a Leaflet style function for choropleth layers
 */
export function createChoroplethStyleFn(
  config: ChoroplethConfig,
  opacity: number
): (properties: Record<string, unknown>) => PathOptions {
  const domain = config.domain ?? [0, 100]

  // Use scale colors from config, or fall back to a default
  const colors = config.scale ?? ['#ffffb2', '#bd0026']
  const colorScale = chroma.scale(colors).domain(domain).mode('lab')

  return (properties: Record<string, unknown>): PathOptions => {
    const value = properties[config.property]
    const numValue = typeof value === 'number' ? value : 0

    return {
      fillColor: colorScale(numValue).hex(),
      fillOpacity: opacity * 0.7,
      color: '#374151', // gray-700
      weight: 1,
      opacity: opacity,
    }
  }
}

/**
 * Create a Leaflet style from a static LayerStyle config
 */
export function createStaticStyle(
  style: LayerStyle | undefined,
  opacity: number
): PathOptions {
  return {
    fillColor: style?.fillColor ?? '#3b82f6', // blue-500
    fillOpacity: (style?.fillOpacity ?? 0.5) * opacity,
    color: style?.color ?? '#1e40af', // blue-800
    weight: style?.weight ?? 1,
    dashArray: style?.dashArray,
    opacity: opacity,
  }
}

/**
 * Get highlight style for hover state
 */
export function getHighlightStyle(): PathOptions {
  return {
    weight: 3,
    color: '#1f2937', // gray-800
    fillOpacity: 0.9,
  }
}

/**
 * Get selected style for clicked features
 */
export function getSelectedStyle(): PathOptions {
  return {
    weight: 4,
    color: '#0ea5e9', // sky-500
    fillOpacity: 0.9,
  }
}
