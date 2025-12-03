import { useLayerStore } from '@/stores/layerStore'
import { getLayerConfig } from '@/data/layerConfig'
import { getLegendStops, createDivergentScale } from '@/lib/colorScales'

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

  // Generate legend stops
  // For voting data, use divergent scale centered at 50%
  const isDivergent = domain[0] === 0 && domain[1] === 100
  let stops: Array<{ value: number; color: string }>

  if (isDivergent) {
    // Create custom stops for divergent scale
    const colorFn = createDivergentScale('voting', domain, 50)
    stops = [0, 25, 50, 75, 100].map(value => ({
      value,
      color: colorFn(value),
    }))
  } else {
    stops = getLegendStops('priority', domain, choropleth.steps)
  }

  return (
    <div className="absolute bottom-8 left-4 z-[1000] rounded-lg bg-white p-4 shadow-lg">
      <h4 className="mb-3 text-sm font-semibold text-gray-900">
        {choropleth.legendTitle}
      </h4>
      <div className="flex flex-col gap-1">
        {stops.map((stop, index) => (
          <div key={index} className="flex items-center gap-2">
            <div
              className="h-4 w-6 rounded border border-gray-200"
              style={{ backgroundColor: stop.color }}
            />
            <span className="text-xs text-gray-600">
              {choropleth.formatValue(stop.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
