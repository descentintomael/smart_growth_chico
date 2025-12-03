import { useFilterStore } from '@/stores/filterStore'
import { useLayerStore } from '@/stores/layerStore'

/**
 * Range slider component for filtering numeric properties
 */
interface RangeSliderProps {
  label: string
  min: number
  max: number
  value: [number, number]
  onChange: (value: [number, number]) => void
  formatValue?: (v: number) => string
}

function RangeSlider({ label, min, max, value, onChange, formatValue }: RangeSliderProps) {
  const format = formatValue ?? ((v: number) => v.toString())

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-xs text-gray-500">
          {format(value[0])} – {format(value[1])}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="range"
          min={min}
          max={max}
          value={value[0]}
          onChange={e => onChange([Number(e.target.value), value[1]])}
          className="h-1 flex-1 cursor-pointer appearance-none rounded-lg bg-gray-200"
          aria-label={`${label} minimum value`}
        />
        <input
          type="range"
          min={min}
          max={max}
          value={value[1]}
          onChange={e => onChange([value[0], Number(e.target.value)])}
          className="h-1 flex-1 cursor-pointer appearance-none rounded-lg bg-gray-200"
          aria-label={`${label} maximum value`}
        />
      </div>
    </div>
  )
}

/**
 * Filter panel for Smart Growth Index layer
 */
function SmartGrowthFilter() {
  const filters = useFilterStore(state => state.filters)
  const setFilter = useFilterStore(state => state.setFilter)
  const clearLayerFilter = useFilterStore(state => state.clearLayerFilter)

  const layerId = 'smart-growth-index'
  const currentFilter = filters[layerId]

  const scoreRange: [number, number] = [
    currentFilter?.property === 'sg_index' ? (currentFilter.min ?? 0) : 0,
    currentFilter?.property === 'sg_index' ? (currentFilter.max ?? 100) : 100,
  ]

  const handleScoreChange = (value: [number, number]) => {
    setFilter(layerId, 'sg_index', value[0], value[1])
  }

  const handleClear = () => {
    clearLayerFilter(layerId)
  }

  const hasFilter = currentFilter !== undefined

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-900">Filter by Score</h4>
        {hasFilter && (
          <button
            onClick={handleClear}
            className="text-xs text-primary-600 hover:text-primary-700"
            aria-label="Clear filter"
          >
            Clear
          </button>
        )}
      </div>

      <RangeSlider
        label="Smart Growth Index"
        min={0}
        max={100}
        value={scoreRange}
        onChange={handleScoreChange}
      />

      <div className="text-xs text-gray-500">
        <p>0-40: Low | 40-60: Moderate | 60-80: Good | 80+: Excellent</p>
      </div>
    </div>
  )
}

export function FilterPanel() {
  const visibleLayers = useLayerStore(state => state.visibleLayers)
  const clearAllFilters = useFilterStore(state => state.clearAllFilters)
  const filters = useFilterStore(state => state.filters)

  const hasSmartGrowth = visibleLayers.has('smart-growth-index')
  const hasAnyFilters = Object.keys(filters).length > 0

  // Only show filter panel if the Smart Growth layer is visible
  if (!hasSmartGrowth) {
    return null
  }

  return (
    <section
      role="region"
      aria-labelledby="filter-panel-heading"
      className="border-t border-gray-200"
    >
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 id="filter-panel-heading" className="text-base font-semibold text-gray-900">
          Filters
        </h3>
        {hasAnyFilters && (
          <button
            onClick={clearAllFilters}
            className="text-xs text-primary-600 hover:text-primary-700"
            aria-label="Clear all filters"
          >
            Clear All
          </button>
        )}
      </div>

      <div className="p-4">
        <SmartGrowthFilter />
      </div>
    </section>
  )
}
