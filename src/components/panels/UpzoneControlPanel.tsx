import { useEffect } from 'react'
import { useUpzoneStore } from '@/stores/upzoneStore'
import { useLayerStore } from '@/stores/layerStore'
import type { UpzoneSummary, UpzoneViewMode } from '@/types'

/**
 * Single value slider component
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
        <span className="text-sm font-semibold text-green-600">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-green-600"
        aria-label={label}
      />
    </div>
  )
}

/**
 * View mode toggle (Current vs Projected)
 */
function ViewModeToggle() {
  const viewMode = useUpzoneStore((state) => state.viewMode)
  const setViewMode = useUpzoneStore((state) => state.setViewMode)

  const modes: { value: UpzoneViewMode; label: string }[] = [
    { value: 'current', label: 'Current' },
    { value: 'projected', label: 'Projected' },
  ]

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">Display Mode</label>
      <div className="flex rounded-lg border border-gray-200 overflow-hidden">
        {modes.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setViewMode(value)}
            className={`flex-1 px-3 py-2 text-sm font-medium transition-colors
              ${
                viewMode === value
                  ? 'bg-green-100 text-green-700'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            aria-pressed={viewMode === value}
          >
            {label}
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-500">
        {viewMode === 'projected'
          ? 'Showing SG Index improvement from upzoning'
          : 'Showing current SG Index values'}
      </p>
    </div>
  )
}

/**
 * Interpolate stats between pre-computed adoption scenarios
 */
function getInterpolatedStats(
  summary: UpzoneSummary | null,
  percent: number
): { parcels: number; newUnits: number; taxIncrease: number; avgSgChange: number } | null {
  if (!summary) return null

  const scenarios = summary.adoption_scenarios
  const breakpoints = [10, 25, 50, 75, 100]

  if (percent <= 0) {
    return { parcels: 0, newUnits: 0, taxIncrease: 0, avgSgChange: 0 }
  }

  // Find surrounding breakpoints for interpolation
  let lower = 0
  let upper = 10

  for (let i = 0; i < breakpoints.length; i++) {
    const bp = breakpoints[i]
    if (bp !== undefined && percent <= bp) {
      upper = bp
      lower = i > 0 ? (breakpoints[i - 1] ?? 0) : 0
      break
    }
    if (i === breakpoints.length - 1) {
      lower = bp ?? 100
      upper = bp ?? 100
    }
  }

  // Linear interpolation factor
  const t = upper === lower ? 1 : (percent - lower) / (upper - lower)

  const lowerData =
    lower === 0
      ? { parcels: 0, acres: 0, tax_increase_annual: 0, new_units: 0, avg_sg_change: 0 }
      : scenarios[lower.toString()]

  const upperData = scenarios[upper.toString()]

  if (!lowerData || !upperData) return null

  return {
    parcels: Math.round(lowerData.parcels + t * (upperData.parcels - lowerData.parcels)),
    newUnits: Math.round(lowerData.new_units + t * (upperData.new_units - lowerData.new_units)),
    taxIncrease:
      lowerData.tax_increase_annual +
      t * (upperData.tax_increase_annual - lowerData.tax_increase_annual),
    avgSgChange:
      lowerData.avg_sg_change + t * (upperData.avg_sg_change - lowerData.avg_sg_change),
  }
}

/**
 * Summary statistics display
 */
interface SummaryStatsProps {
  stats: {
    parcels: number
    newUnits: number
    taxIncrease: number
    avgSgChange: number
  } | null
}

function SummaryStats({ stats }: SummaryStatsProps) {
  if (!stats) {
    return (
      <div className="rounded-lg bg-gray-50 p-4">
        <p className="text-sm text-gray-500">Loading summary data...</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg bg-green-50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-900">Projected Impact</h4>
      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="text-xs text-gray-500">Parcels Upzoned</dt>
          <dd className="text-lg font-semibold text-gray-900">
            {stats.parcels.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">New Housing Units</dt>
          <dd className="text-lg font-semibold text-green-600">
            +{stats.newUnits.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Annual Tax Increase</dt>
          <dd className="text-lg font-semibold text-green-600">
            +${(stats.taxIncrease / 1e6).toFixed(1)}M
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Avg SG Index Change</dt>
          <dd className="text-lg font-semibold text-green-600">+{stats.avgSgChange.toFixed(1)}</dd>
        </div>
      </dl>
    </div>
  )
}

/**
 * Tier information display
 */
function TierInfo() {
  return (
    <div className="text-xs text-gray-500 space-y-1">
      <p className="font-medium text-gray-700">Priority Tiers:</p>
      <ul className="space-y-0.5 pl-2">
        <li>
          <span className="font-medium">1:</span> R1 near opportunity sites → R3
        </li>
        <li>
          <span className="font-medium">2:</span> R1 near bike facilities → R2
        </li>
        <li>
          <span className="font-medium">3:</span> Other R1 → R2
        </li>
        <li>
          <span className="font-medium">4:</span> R2 → R3
        </li>
      </ul>
    </div>
  )
}

/**
 * Main control panel for upzone scenario
 */
export function UpzoneControlPanel() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const layerOpacity = useLayerStore((state) => state.layerOpacity)
  const setLayerOpacity = useLayerStore((state) => state.setLayerOpacity)

  const adoptionPercent = useUpzoneStore((state) => state.adoptionPercent)
  const setAdoptionPercent = useUpzoneStore((state) => state.setAdoptionPercent)
  const summary = useUpzoneStore((state) => state.summary)
  const setSummary = useUpzoneStore((state) => state.setSummary)
  const summaryLoading = useUpzoneStore((state) => state.summaryLoading)
  const setSummaryLoading = useUpzoneStore((state) => state.setSummaryLoading)

  const isVisible = visibleLayers.has('upzone-scenario')
  const opacity = layerOpacity['upzone-scenario'] ?? 1

  // Load summary data on mount (only once)
  useEffect(() => {
    if (!summary && !summaryLoading) {
      setSummaryLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/upzone-scenario-summary.json`)
        .then((res) => res.json())
        .then((data) => setSummary(data as UpzoneSummary))
        .catch((err) => {
          console.error('Failed to load upzone summary:', err)
          setSummaryLoading(false)
        })
    }
  }, [summary, summaryLoading, setSummary, setSummaryLoading])

  // Don't render if layer is not visible
  if (!isVisible) {
    return null
  }

  // Interpolate stats based on current adoption percent
  const interpolatedStats = getInterpolatedStats(summary, adoptionPercent)

  return (
    <section
      role="region"
      aria-labelledby="upzone-control-heading"
      className="border-t border-gray-200"
    >
      <div className="border-b border-gray-200 px-4 py-3">
        <h3 id="upzone-control-heading" className="text-base font-semibold text-gray-900">
          Upzone Scenario
        </h3>
        <p className="text-xs text-gray-500 mt-0.5">What-if analysis for R1 upzoning</p>
      </div>

      <div className="space-y-5 p-4">
        {/* View mode toggle */}
        <ViewModeToggle />

        {/* Adoption slider */}
        <Slider
          label="Adoption Rate"
          value={adoptionPercent}
          min={0}
          max={100}
          step={1}
          onChange={setAdoptionPercent}
          formatValue={(v) => `${v}%`}
        />

        {/* Layer opacity */}
        <Slider
          label="Layer Opacity"
          value={Math.round(opacity * 100)}
          min={0}
          max={100}
          onChange={(v) => setLayerOpacity('upzone-scenario', v / 100)}
          formatValue={(v) => `${v}%`}
        />

        {/* Summary statistics */}
        <SummaryStats stats={interpolatedStats} />

        {/* Tier legend */}
        <TierInfo />
      </div>
    </section>
  )
}
