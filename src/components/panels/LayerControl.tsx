import { useLayerStore } from '@/stores/layerStore'

export function LayerControl() {
  const layerOpacity = useLayerStore(state => state.layerOpacity)
  const setLayerOpacity = useLayerStore(state => state.setLayerOpacity)

  const opacity = layerOpacity['smart-growth-index'] ?? 1

  return (
    <section
      role="region"
      aria-labelledby="layer-control-heading"
      className="flex flex-col"
    >
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 id="layer-control-heading" className="text-base font-semibold text-gray-900">
          Smart Growth Index
        </h3>
      </div>

      <div className="p-4">
        <p className="mb-4 text-sm text-gray-600">
          Parcel-level scores (0-100) based on fiscal productivity, land utilization,
          infrastructure access, zoning headroom, and location efficiency.
        </p>

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
            onChange={e => setLayerOpacity('smart-growth-index', Number(e.target.value) / 100)}
            className="h-1 w-24 cursor-pointer appearance-none rounded-lg bg-gray-200"
            aria-label="Layer opacity"
          />
          <span className="w-8 text-xs text-gray-500">{Math.round(opacity * 100)}%</span>
        </div>
      </div>
    </section>
  )
}
