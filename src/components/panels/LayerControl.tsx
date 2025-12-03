import { useLayerStore } from '@/stores/layerStore'
import { LAYER_CONFIGS } from '@/data/layerConfig'

// Layer options for the toggle
const LAYER_OPTIONS = [
  {
    id: 'smart-growth-index',
    name: 'Current Index',
    description: 'Current Smart Growth Index scores',
  },
  {
    id: 'upzone-scenario',
    name: 'Upzone Scenario',
    description: 'What-if upzoning analysis',
  },
] as const

type LayerId = (typeof LAYER_OPTIONS)[number]['id']

export function LayerControl() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const toggleLayer = useLayerStore((state) => state.toggleLayer)
  const layerOpacity = useLayerStore((state) => state.layerOpacity)
  const setLayerOpacity = useLayerStore((state) => state.setLayerOpacity)

  // Find which layer is currently active
  const activeLayer = LAYER_OPTIONS.find((opt) => visibleLayers.has(opt.id))?.id ?? 'smart-growth-index'
  const activeConfig = LAYER_CONFIGS.find((c) => c.id === activeLayer)
  const opacity = layerOpacity[activeLayer] ?? 1

  // Switch to a specific layer (mutually exclusive)
  const switchToLayer = (layerId: LayerId) => {
    // Turn off other layers, turn on this one
    LAYER_OPTIONS.forEach((opt) => {
      const isTarget = opt.id === layerId
      const isCurrentlyVisible = visibleLayers.has(opt.id)

      if (isTarget && !isCurrentlyVisible) {
        toggleLayer(opt.id)
      } else if (!isTarget && isCurrentlyVisible) {
        toggleLayer(opt.id)
      }
    })
  }

  return (
    <section role="region" aria-labelledby="layer-control-heading" className="flex flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 id="layer-control-heading" className="text-base font-semibold text-gray-900">
          View Mode
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Layer toggle buttons */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          {LAYER_OPTIONS.map((option) => (
            <button
              key={option.id}
              onClick={() => switchToLayer(option.id)}
              className={`flex-1 px-3 py-2 text-sm font-medium transition-colors
                ${
                  activeLayer === option.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              aria-pressed={activeLayer === option.id}
            >
              {option.name}
            </button>
          ))}
        </div>

        {/* Layer description */}
        <p className="text-sm text-gray-600">{activeConfig?.description}</p>

        {/* Opacity slider (only show for Smart Growth Index - upzone has its own in control panel) */}
        {activeLayer === 'smart-growth-index' && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-500" htmlFor="opacity-slider">
              Opacity
            </label>
            <input
              id="opacity-slider"
              type="range"
              min={0}
              max={100}
              value={Math.round(opacity * 100)}
              onChange={(e) => setLayerOpacity(activeLayer, Number(e.target.value) / 100)}
              className="h-1 w-24 cursor-pointer appearance-none rounded-lg bg-gray-200"
              aria-label="Layer opacity"
            />
            <span className="w-8 text-xs text-gray-500">{Math.round(opacity * 100)}%</span>
          </div>
        )}
      </div>
    </section>
  )
}
