import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useCommercialViabilityStore } from '@/stores/commercialViabilityStore'
import { useLayerStore } from '@/stores/layerStore'
import type { CommercialViabilitySummary } from '@/types'

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
        <span className="text-sm font-semibold text-emerald-600">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-emerald-600"
        aria-label={label}
      />
    </div>
  )
}

/**
 * Get interpolated stats between pre-computed adoption scenarios
 */
function getInterpolatedStats(
  summary: CommercialViabilitySummary | null,
  percent: number
): { newResidents: number; totalViable: number; newEnabled: number } | null {
  if (!summary) return null

  const aggregates = summary.aggregate_totals

  if (percent <= 0) {
    return {
      newResidents: 0,
      totalViable: aggregates.current.total_businesses_viable,
      newEnabled: 0,
    }
  }

  // Find surrounding breakpoints for interpolation
  const breakpoints = [25, 50, 75, 100]
  let lower = 0
  let upper = 25

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
      ? { new_residents: 0, total_businesses_viable: aggregates.current.total_businesses_viable, new_businesses_enabled: 0 }
      : (aggregates[lower.toString()] as {
          new_residents?: number
          total_businesses_viable?: number
          new_businesses_enabled?: number
        })

  const upperData = aggregates[upper.toString()] as {
    new_residents?: number
    total_businesses_viable?: number
    new_businesses_enabled?: number
  }

  if (!lowerData || !upperData) return null

  const lowerResidents = lowerData.new_residents ?? 0
  const upperResidents = upperData.new_residents ?? 0
  const lowerViable = lowerData.total_businesses_viable ?? aggregates.current.total_businesses_viable
  const upperViable = upperData.total_businesses_viable ?? aggregates.current.total_businesses_viable
  const lowerEnabled = lowerData.new_businesses_enabled ?? 0
  const upperEnabled = upperData.new_businesses_enabled ?? 0

  return {
    newResidents: Math.round(lowerResidents + t * (upperResidents - lowerResidents)),
    totalViable: Math.round(lowerViable + t * (upperViable - lowerViable)),
    newEnabled: Math.round(lowerEnabled + t * (upperEnabled - lowerEnabled)),
  }
}

/**
 * Summary statistics display
 */
interface SummaryStatsProps {
  stats: {
    newResidents: number
    totalViable: number
    newEnabled: number
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
    <div className="rounded-lg bg-emerald-50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-900">Projected Impact</h4>
      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="text-xs text-gray-500">New Residents</dt>
          <dd className="text-lg font-semibold text-emerald-600">
            +{stats.newResidents.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Total Viable</dt>
          <dd className="text-lg font-semibold text-gray-900">
            {stats.totalViable}
          </dd>
        </div>
        <div className="col-span-2">
          <dt className="text-xs text-gray-500">New Business Locations Enabled</dt>
          <dd className="text-lg font-semibold text-emerald-600">
            +{stats.newEnabled}
          </dd>
        </div>
      </dl>
    </div>
  )
}

/**
 * Business types info
 */
function BusinessTypesInfo() {
  return (
    <div className="text-xs text-gray-500 space-y-1">
      <p className="font-medium text-gray-700">Business Types Tracked:</p>
      <ul className="space-y-0.5 pl-2 grid grid-cols-2 gap-x-2">
        <li>Coffee Shop</li>
        <li>Small Restaurant</li>
        <li>Convenience Store</li>
        <li>Neighborhood Grocery</li>
        <li>Pharmacy</li>
        <li>Medium Grocery</li>
        <li>Fitness Center</li>
        <li>Hardware Store</li>
      </ul>
    </div>
  )
}

/**
 * Main control panel for commercial viability
 */
export function CommercialViabilityControlPanel() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const layerOpacity = useLayerStore((state) => state.layerOpacity)
  const setLayerOpacity = useLayerStore((state) => state.setLayerOpacity)

  const adoptionPercent = useCommercialViabilityStore((state) => state.adoptionPercent)
  const setAdoptionPercent = useCommercialViabilityStore((state) => state.setAdoptionPercent)
  const summary = useCommercialViabilityStore((state) => state.summary)
  const setSummary = useCommercialViabilityStore((state) => state.setSummary)
  const summaryLoading = useCommercialViabilityStore((state) => state.summaryLoading)
  const setSummaryLoading = useCommercialViabilityStore((state) => state.setSummaryLoading)

  const isVisible = visibleLayers.has('commercial-viability')
  const opacity = layerOpacity['commercial-viability'] ?? 1

  // Load summary data on mount (only once)
  useEffect(() => {
    if (!summary && !summaryLoading) {
      setSummaryLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/commercial-viability-summary.json`)
        .then((res) => res.json())
        .then((data) => setSummary(data as CommercialViabilitySummary))
        .catch((err) => {
          console.error('Failed to load commercial viability summary:', err)
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
      aria-labelledby="commercial-viability-control-heading"
      className="border-t border-gray-200"
    >
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 id="commercial-viability-control-heading" className="text-base font-semibold text-gray-900">
              Commercial Viability
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">Business viability at opportunity sites</p>
          </div>
          <Link
            to="/methodology/commercial-viability"
            className="text-xs text-primary-600 hover:text-primary-700 hover:underline whitespace-nowrap"
          >
            View Methodology
          </Link>
        </div>
      </div>

      <div className="space-y-5 p-4">
        {/* Adoption slider */}
        <Slider
          label="Upzone Adoption Rate"
          value={adoptionPercent}
          min={0}
          max={100}
          step={5}
          onChange={setAdoptionPercent}
          formatValue={(v) => `${v}%`}
        />

        {/* Layer opacity */}
        <Slider
          label="Layer Opacity"
          value={Math.round(opacity * 100)}
          min={0}
          max={100}
          onChange={(v) => setLayerOpacity('commercial-viability', v / 100)}
          formatValue={(v) => `${v}%`}
        />

        {/* Summary statistics */}
        <SummaryStats stats={interpolatedStats} />

        {/* Business types legend */}
        <BusinessTypesInfo />
      </div>
    </section>
  )
}
