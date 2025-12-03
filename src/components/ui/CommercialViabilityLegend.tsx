import chroma from 'chroma-js'
import { useLayerStore } from '@/stores/layerStore'
import {
  COMMERCIAL_VIABILITY_SCALE,
  COMMERCIAL_VIABILITY_DOMAIN,
} from '@/components/layers/CommercialViabilityLayer'

/**
 * Map legend for the commercial viability layer
 * Shows color scale for viable business types
 */
export function CommercialViabilityLegend() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)

  // Only show if commercial viability layer is visible
  if (!visibleLayers.has('commercial-viability')) {
    return null
  }

  // Create color scale
  const colorScale = chroma
    .scale(COMMERCIAL_VIABILITY_SCALE)
    .domain(COMMERCIAL_VIABILITY_DOMAIN)
    .mode('lab')

  // Generate legend stops (0 to 8)
  const stops = [0, 2, 4, 6, 8].map((value) => ({
    value,
    color: colorScale(value).hex(),
  }))

  return (
    <aside
      role="complementary"
      aria-labelledby="commercial-viability-legend-heading"
      className="map-legend absolute bottom-8 left-4 z-[1000] rounded-lg bg-white p-4 shadow-lg"
    >
      <h4
        id="commercial-viability-legend-heading"
        className="mb-3 text-sm font-semibold text-gray-900"
      >
        Viable Business Types
      </h4>

      {/* Choropleth color scale */}
      <div className="mb-3 flex flex-col gap-1" role="list" aria-label="Color scale values">
        {stops.map((stop, index) => (
          <div key={index} className="flex items-center gap-2" role="listitem">
            <div
              className="h-4 w-6 rounded border border-gray-200"
              style={{ backgroundColor: stop.color }}
              aria-hidden="true"
            />
            <span className="text-xs text-gray-600">{stop.value}</span>
          </div>
        ))}
      </div>

      {/* Info note */}
      <div className="border-t border-gray-200 pt-3">
        <p className="text-xs text-gray-500">
          Sites colored by total business types viable at selected adoption rate
        </p>
      </div>
    </aside>
  )
}
