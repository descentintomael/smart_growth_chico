import { useSelectionStore } from '@/stores/selectionStore'
import { getLayerConfig } from '@/data/layerConfig'

/**
 * Format a property value for display
 */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  return String(value)
}

export function InfoPanel() {
  const selectedFeature = useSelectionStore(state => state.selectedFeature)
  const selectedLayerId = useSelectionStore(state => state.selectedLayerId)
  const clearSelection = useSelectionStore(state => state.clearSelection)

  if (!selectedFeature) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-6 text-center">
        <svg
          className="mb-4 h-12 w-12 text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
          />
        </svg>
        <p className="text-sm text-gray-500">Click on a feature to see details</p>
      </div>
    )
  }

  const properties = selectedFeature.properties ?? {}
  const config = selectedLayerId ? getLayerConfig(selectedLayerId) : null

  // Get title from popup config or use default
  let title = 'Feature Details'
  if (config?.popup?.title) {
    title = config.popup.title.replace(/\{(\w+)\}/g, (_, key) => {
      const value = properties[key]
      return value != null ? String(value) : ''
    })
  }

  // Get fields from popup config or show all properties
  const fields: Array<{ label: string; property: string; format?: (v: unknown) => string }> =
    config?.popup?.fields ?? Object.keys(properties).map(key => ({
      label: key,
      property: key,
    }))

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        <button
          onClick={clearSelection}
          className="text-gray-400 hover:text-gray-500"
          aria-label="Close"
        >
          <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <dl className="space-y-3">
          {fields.map(field => {
            const rawValue = properties[field.property]
            const displayValue = field.format
              ? field.format(rawValue)
              : formatValue(rawValue)

            return (
              <div key={field.property}>
                <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">
                  {field.label}
                </dt>
                <dd className="mt-1 text-sm text-gray-900">{displayValue}</dd>
              </div>
            )
          })}
        </dl>
      </div>
    </div>
  )
}
