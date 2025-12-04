import { useEffect } from 'react'
import { useUnderUtilizationStore } from '@/stores/underUtilizationStore'
import { useLayerStore } from '@/stores/layerStore'
import type { UnderUtilizationMetric, UnderUtilizationSummary } from '@/types'
import { UnderUtilizationLegend } from './UnderUtilizationLegend'

// Metric options for selector
const METRIC_OPTIONS: { value: UnderUtilizationMetric; label: string; description: string }[] = [
  {
    value: 'composite',
    label: 'Composite',
    description: 'Weighted combination of all metrics',
  },
  {
    value: 'vertical',
    label: 'Vertical (FAR)',
    description: 'Floor area ratio vs. allowed FAR',
  },
  {
    value: 'improvement',
    label: 'Improvement',
    description: 'Land value exceeds building value',
  },
  {
    value: 'density',
    label: 'Density',
    description: 'Zoning headroom unused',
  },
  {
    value: 'upzone',
    label: 'Upzone Potential',
    description: 'Units possible from R1→R2',
  },
]

/**
 * Slider component
 */
interface SliderProps {
  label: string
  value: number
  min: number
  max: number
  step?: number
  onChange: (value: number) => void
  formatValue?: (v: number) => string
}

function Slider({ label, value, min, max, step = 1, onChange, formatValue }: SliderProps) {
  const format = formatValue ?? ((v: number) => v.toString())

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm font-semibold text-orange-600">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-orange-600"
        aria-label={label}
      />
    </div>
  )
}

/**
 * Metric selector
 */
function MetricSelector() {
  const selectedMetric = useUnderUtilizationStore((state) => state.selectedMetric)
  const setMetric = useUnderUtilizationStore((state) => state.setMetric)

  const currentOption = METRIC_OPTIONS.find((o) => o.value === selectedMetric)

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">Metric</label>
      <select
        value={selectedMetric}
        onChange={(e) => setMetric(e.target.value as UnderUtilizationMetric)}
        className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
      >
        {METRIC_OPTIONS.map(({ value, label }) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      {currentOption && (
        <p className="text-xs text-gray-500">{currentOption.description}</p>
      )}
    </div>
  )
}

/**
 * Summary statistics display
 */
interface SummaryStatsProps {
  summary: UnderUtilizationSummary | null
}

function SummaryStats({ summary }: SummaryStatsProps) {
  if (!summary) {
    return (
      <div className="rounded-lg bg-gray-50 p-4">
        <p className="text-sm text-gray-500">Loading summary data...</p>
      </div>
    )
  }

  const highlights = summary.advocacy_highlights

  return (
    <div className="rounded-lg bg-orange-50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-900">Key Findings</h4>
      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="text-xs text-gray-500">Underutilized Parcels</dt>
          <dd className="text-lg font-semibold text-gray-900">
            {highlights.total_underutilized_parcels.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Underutilized Acres</dt>
          <dd className="text-lg font-semibold text-gray-900">
            {highlights.total_underutilized_acres.toFixed(0)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Foregone Units</dt>
          <dd className="text-lg font-semibold text-orange-600">
            {highlights.total_foregone_units.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Foregone Tax Revenue</dt>
          <dd className="text-lg font-semibold text-orange-600">
            ${(highlights.potential_annual_tax_increase / 1e6).toFixed(1)}M
          </dd>
        </div>
      </dl>
    </div>
  )
}

/**
 * Methodology info
 */
function MethodologyInfo() {
  return (
    <div className="text-xs text-gray-500 space-y-1">
      <p className="font-medium text-gray-700">Tier Thresholds:</p>
      <ul className="space-y-0.5 pl-2">
        <li>
          <span className="font-medium text-gray-600">Low:</span> &lt;40
        </li>
        <li>
          <span className="font-medium text-yellow-600">Moderate:</span> 40-60
        </li>
        <li>
          <span className="font-medium text-orange-600">High:</span> 60-80
        </li>
        <li>
          <span className="font-medium text-red-600">Severe:</span> &gt;80
        </li>
      </ul>
    </div>
  )
}

/**
 * Main control panel for under-utilization layer
 */
export function UnderUtilizationControlPanel() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const layerOpacity = useLayerStore((state) => state.layerOpacity)
  const setLayerOpacity = useLayerStore((state) => state.setLayerOpacity)

  const summary = useUnderUtilizationStore((state) => state.summary)
  const setSummary = useUnderUtilizationStore((state) => state.setSummary)
  const summaryLoading = useUnderUtilizationStore((state) => state.summaryLoading)
  const setSummaryLoading = useUnderUtilizationStore((state) => state.setSummaryLoading)

  const isVisible = visibleLayers.has('under-utilization')
  const opacity = layerOpacity['under-utilization'] ?? 1

  // Load summary data on mount
  useEffect(() => {
    if (!summary && !summaryLoading) {
      setSummaryLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/under-utilization-summary.json`)
        .then((res) => res.json())
        .then((data) => setSummary(data as UnderUtilizationSummary))
        .catch((err) => {
          console.error('Failed to load under-utilization summary:', err)
          setSummaryLoading(false)
        })
    }
  }, [summary, summaryLoading, setSummary, setSummaryLoading])

  // Don't render if layer is not visible
  if (!isVisible) {
    return null
  }

  return (
    <section
      role="region"
      aria-labelledby="under-utilization-control-heading"
      className="border-t border-gray-200"
    >
      <div className="border-b border-gray-200 px-4 py-3">
        <h3 id="under-utilization-control-heading" className="text-base font-semibold text-gray-900">
          Under-Utilization Analysis
        </h3>
        <p className="text-xs text-gray-500 mt-0.5">Identify parcels with development potential</p>
      </div>

      <div className="space-y-5 p-4">
        {/* Metric selector */}
        <MetricSelector />

        {/* Layer opacity */}
        <Slider
          label="Layer Opacity"
          value={Math.round(opacity * 100)}
          min={0}
          max={100}
          onChange={(v) => setLayerOpacity('under-utilization', v / 100)}
          formatValue={(v) => `${v}%`}
        />

        {/* Legend */}
        <UnderUtilizationLegend />

        {/* Summary statistics */}
        <SummaryStats summary={summary} />

        {/* Methodology */}
        <MethodologyInfo />
      </div>
    </section>
  )
}
