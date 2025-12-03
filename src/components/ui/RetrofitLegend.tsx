import chroma from 'chroma-js'
import { useLayerStore } from '@/stores/layerStore'
import { RETROFIT_COLOR_SCALE } from '@/components/layers/RetrofitLayer'
import type { RetrofitLayerId } from '@/types'

// Max units for each layer (same as in RetrofitLayer)
const MAX_UNITS: Record<RetrofitLayerId, number> = {
  'parking-retrofit': 400,
  'vacant-infill': 1300,
  'commercial-retrofit': 450,
}

const LAYER_LABELS: Record<RetrofitLayerId, string> = {
  'parking-retrofit': 'Potential Housing Units',
  'vacant-infill': 'Potential Housing Units',
  'commercial-retrofit': 'Potential Housing Units',
}

const RETROFIT_LAYERS: RetrofitLayerId[] = [
  'parking-retrofit',
  'vacant-infill',
  'commercial-retrofit',
]

export function RetrofitLegend() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)

  // Find active retrofit layer
  const activeLayer = RETROFIT_LAYERS.find((id) => visibleLayers.has(id))

  // Only show if a retrofit layer is visible
  if (!activeLayer) {
    return null
  }

  const maxUnits = MAX_UNITS[activeLayer]

  // Create color scale
  const colorScale = chroma.scale(RETROFIT_COLOR_SCALE).domain([0, maxUnits]).mode('lab')

  // Generate legend stops
  const numStops = 5
  const stops = Array.from({ length: numStops }, (_, i) => {
    const value = Math.round((maxUnits * i) / (numStops - 1))
    return {
      value,
      color: colorScale(value).hex(),
    }
  })

  return (
    <aside
      role="complementary"
      aria-labelledby="retrofit-legend-heading"
      className="map-legend absolute bottom-8 left-4 z-[1000] rounded-lg bg-white p-4 shadow-lg"
    >
      <h4
        id="retrofit-legend-heading"
        className="mb-3 text-sm font-semibold text-gray-900"
      >
        {LAYER_LABELS[activeLayer]}
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
            <span className="text-xs text-gray-600">
              {stop.value.toLocaleString()}
              {index === stops.length - 1 ? '+' : ''}
            </span>
          </div>
        ))}
      </div>

      {/* Info note */}
      <div className="border-t border-gray-200 pt-3">
        <p className="text-xs text-gray-500">
          Parcels colored by potential housing units if developed
        </p>
      </div>
    </aside>
  )
}
