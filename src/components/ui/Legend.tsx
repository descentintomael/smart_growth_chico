import chroma from 'chroma-js'
import { useLayerStore } from '@/stores/layerStore'
import { getLayerConfig } from '@/data/layerConfig'

/**
 * Map legend showing color scale for the active choropleth layer
 */
export function Legend() {
  const visibleLayers = useLayerStore(state => state.visibleLayers)

  // Find first visible layer with choropleth config
  const activeLayerId = [...visibleLayers].find(id => {
    const config = getLayerConfig(id)
    return config?.choropleth
  })

  if (!activeLayerId) {
    return null
  }

  const config = getLayerConfig(activeLayerId)
  if (!config?.choropleth) {
    return null
  }

  const { choropleth } = config
  const domain = choropleth.domain ?? [0, 100]
  const steps = choropleth.steps ?? 5

  // Use the scale colors directly from config
  const colors = choropleth.scale ?? ['#ffffb2', '#bd0026']
  const colorScale = chroma.scale(colors).domain(domain).mode('lab')

  // Generate legend stops
  const stepSize = (domain[1] - domain[0]) / (steps - 1)
  const stops = Array.from({ length: steps }, (_, i) => {
    const value = domain[0] + stepSize * i
    return { value, color: colorScale(value).hex() }
  })

  return (
    <aside
      role="complementary"
      aria-labelledby="legend-heading"
      className="map-legend absolute bottom-8 left-4 z-[1000] rounded-lg bg-white p-4 shadow-lg"
    >
      <h4 id="legend-heading" className="mb-3 text-sm font-semibold text-gray-900">
        {choropleth.legendTitle}
      </h4>
      <div className="flex flex-col gap-1" role="list" aria-label="Color scale values">
        {stops.map((stop, index) => (
          <div key={index} className="flex items-center gap-2" role="listitem">
            <div
              className="h-4 w-6 rounded border border-gray-200"
              style={{ backgroundColor: stop.color }}
              aria-hidden="true"
            />
            <span className="text-xs text-gray-600">
              {choropleth.formatValue(stop.value)}
            </span>
          </div>
        ))}
      </div>
    </aside>
  )
}
