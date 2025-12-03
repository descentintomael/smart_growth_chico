import chroma from 'chroma-js'
import { useLayerStore } from '@/stores/layerStore'
import { useUpzoneStore } from '@/stores/upzoneStore'
import { DELTA_SG_SCALE, DELTA_SG_DOMAIN } from '@/components/layers/UpzoneScenarioLayer'

/**
 * Map legend for the upzone scenario layer
 * Shows color scale and symbol explanations
 */
export function UpzoneLegend() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const viewMode = useUpzoneStore((state) => state.viewMode)

  // Only show if upzone scenario layer is visible
  if (!visibleLayers.has('upzone-scenario')) {
    return null
  }

  // Create color scale
  const colorScale = chroma.scale(DELTA_SG_SCALE).domain(DELTA_SG_DOMAIN).mode('lab')

  // Generate legend stops
  const stops = [0, 5, 10, 15, 20].map((value) => ({
    value,
    color: colorScale(value).hex(),
  }))

  const legendTitle = viewMode === 'projected' ? 'SG Index Change' : 'SG Index (scaled)'

  return (
    <aside
      role="complementary"
      aria-labelledby="upzone-legend-heading"
      className="map-legend absolute bottom-8 left-4 z-[1000] rounded-lg bg-white p-4 shadow-lg"
    >
      <h4 id="upzone-legend-heading" className="mb-3 text-sm font-semibold text-gray-900">
        {legendTitle}
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
              {viewMode === 'projected' ? `+${stop.value}` : stop.value * 5}
            </span>
          </div>
        ))}
      </div>

      {/* Symbol legend */}
      <div className="border-t border-gray-200 pt-3 space-y-2">
        <div className="flex items-center gap-2">
          <div
            className="h-4 w-6 rounded"
            style={{
              border: '2px dashed #6b7280',
              backgroundColor: 'transparent',
            }}
            aria-hidden="true"
          />
          <span className="text-xs text-gray-600">Eligible (not adopted)</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="h-4 w-6 rounded"
            style={{
              border: '1px solid #d1d5db',
              backgroundColor: 'transparent',
            }}
            aria-hidden="true"
          />
          <span className="text-xs text-gray-600">Not eligible</span>
        </div>
      </div>
    </aside>
  )
}
