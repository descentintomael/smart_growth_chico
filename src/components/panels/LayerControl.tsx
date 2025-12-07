import { useLayerStore } from '@/stores/layerStore'
import { LAYER_CONFIGS } from '@/data/layerConfig'

// Layer options grouped by category
const LAYER_GROUPS = [
  {
    label: 'Current Conditions',
    options: [
      { id: 'smart-growth-index', name: 'Smart Growth Index' },
      { id: 'under-utilization', name: 'Under-Utilization' },
      { id: 'fire-risk-index', name: 'Fire Risk Index' },
    ],
  },
  {
    label: 'Upzoning Scenarios',
    options: [
      { id: 'upzone-scenario', name: 'Upzone Scenario' },
      { id: 'commercial-viability', name: 'Commercial Viability' },
    ],
  },
  {
    label: 'Retrofit Scenarios',
    options: [
      { id: 'parking-retrofit', name: 'Parking Retrofit' },
      { id: 'vacant-infill', name: 'Vacant Infill' },
      { id: 'commercial-retrofit', name: 'Commercial Retrofit' },
    ],
  },
] as const

// Flatten all layer IDs for type safety
const ALL_LAYER_IDS = LAYER_GROUPS.flatMap((group) => group.options.map((opt) => opt.id))
type LayerId = (typeof ALL_LAYER_IDS)[number]

export function LayerControl() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const toggleLayer = useLayerStore((state) => state.toggleLayer)
  const layerOpacity = useLayerStore((state) => state.layerOpacity)
  const setLayerOpacity = useLayerStore((state) => state.setLayerOpacity)

  // Find which layer is currently active
  const activeLayer =
    ALL_LAYER_IDS.find((id) => visibleLayers.has(id)) ?? 'smart-growth-index'
  const activeConfig = LAYER_CONFIGS.find((c) => c.id === activeLayer)
  const opacity = layerOpacity[activeLayer] ?? 1

  // Switch to a specific layer (mutually exclusive)
  const switchToLayer = (layerId: string) => {
    const targetId = layerId as LayerId
    // Turn off other layers, turn on this one
    ALL_LAYER_IDS.forEach((id) => {
      const isTarget = id === targetId
      const isCurrentlyVisible = visibleLayers.has(id)

      if (isTarget && !isCurrentlyVisible) {
        toggleLayer(id)
      } else if (!isTarget && isCurrentlyVisible) {
        toggleLayer(id)
      }
    })
  }

  // Handle dropdown change
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    switchToLayer(e.target.value)
  }

  return (
    <section role="region" aria-labelledby="layer-control-heading" className="flex flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 id="layer-control-heading" className="text-base font-semibold text-gray-900">
          View Mode
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Layer dropdown selector */}
        <div className="space-y-1">
          <label htmlFor="layer-select" className="sr-only">
            Select view mode
          </label>
          <select
            id="layer-select"
            value={activeLayer}
            onChange={handleSelectChange}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-900 shadow-sm hover:bg-gray-50 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {LAYER_GROUPS.map((group) => (
              <optgroup key={group.label} label={group.label}>
                {group.options.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Layer description */}
        <p className="text-sm text-gray-600">{activeConfig?.description}</p>

        {/* Opacity slider (only show for Smart Growth Index - others have their own in control panels) */}
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
