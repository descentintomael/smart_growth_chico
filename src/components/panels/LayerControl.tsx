import { useLayerStore } from '@/stores/layerStore'
import { getLayersByGroup } from '@/data/layerConfig'
import type { LayerGroup, LayerConfig } from '@/types'

const LAYER_GROUPS: LayerGroup[] = ['voting', 'planning', 'infrastructure', 'demographics']

const GROUP_LABELS: Record<LayerGroup, string> = {
  voting: 'Voting Data',
  planning: 'Planning',
  infrastructure: 'Infrastructure',
  demographics: 'Demographics',
}

interface LayerToggleProps {
  config: LayerConfig
}

function LayerToggle({ config }: LayerToggleProps) {
  const visibleLayers = useLayerStore(state => state.visibleLayers)
  const layerOpacity = useLayerStore(state => state.layerOpacity)
  const toggleLayer = useLayerStore(state => state.toggleLayer)
  const setLayerOpacity = useLayerStore(state => state.setLayerOpacity)

  const isVisible = visibleLayers.has(config.id)
  const opacity = layerOpacity[config.id] ?? 1

  return (
    <div className="py-2">
      <label className="flex cursor-pointer items-center gap-3">
        <input
          type="checkbox"
          checked={isVisible}
          onChange={() => toggleLayer(config.id)}
          className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        />
        <div className="flex-1">
          <span className="text-sm font-medium text-gray-700">{config.name}</span>
          {config.description && (
            <p className="text-xs text-gray-500">{config.description}</p>
          )}
        </div>
      </label>

      {/* Opacity slider - only show when layer is visible */}
      {isVisible && (
        <div className="mt-2 flex items-center gap-2 pl-7">
          <label className="text-xs text-gray-500">Opacity</label>
          <input
            type="range"
            min={0}
            max={100}
            value={Math.round(opacity * 100)}
            onChange={e => setLayerOpacity(config.id, Number(e.target.value) / 100)}
            className="h-1 w-20 cursor-pointer appearance-none rounded-lg bg-gray-200"
          />
          <span className="w-8 text-xs text-gray-500">{Math.round(opacity * 100)}%</span>
        </div>
      )}
    </div>
  )
}

interface LayerGroupSectionProps {
  group: LayerGroup
}

function LayerGroupSection({ group }: LayerGroupSectionProps) {
  const layers = getLayersByGroup(group)

  if (layers.length === 0) {
    return null
  }

  return (
    <div className="mb-4">
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        {GROUP_LABELS[group]}
      </h4>
      <div className="divide-y divide-gray-100">
        {layers.map(config => (
          <LayerToggle key={config.id} config={config} />
        ))}
      </div>
    </div>
  )
}

export function LayerControl() {
  const resetLayers = useLayerStore(state => state.resetLayers)

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 className="text-base font-semibold text-gray-900">Layers</h3>
        <button
          onClick={resetLayers}
          className="text-xs text-primary-600 hover:text-primary-700"
        >
          Reset
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {LAYER_GROUPS.map(group => (
          <LayerGroupSection key={group} group={group} />
        ))}
      </div>
    </div>
  )
}
