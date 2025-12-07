import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useFireRiskStore } from '@/stores/fireRiskStore'
import { useLayerStore } from '@/stores/layerStore'
import type { FireRiskSummary, FireRiskTier } from '@/types'
import { FireRiskLegend } from './FireRiskLegend'
import { FIRE_TIER_COLORS } from '@/components/layers/FireRiskLayer'

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
        <span className="text-sm font-semibold text-red-600">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-red-600"
        aria-label={label}
      />
    </div>
  )
}

/**
 * Tier distribution display
 */
interface TierDistributionProps {
  summary: FireRiskSummary | null
}

function TierDistribution({ summary }: TierDistributionProps) {
  if (!summary) {
    return (
      <div className="rounded-lg bg-gray-50 p-4">
        <p className="text-sm text-gray-500">Loading distribution data...</p>
      </div>
    )
  }

  const tiers: FireRiskTier[] = ['Low', 'Moderate', 'High', 'Extreme']
  const total = summary.total_parcels_analyzed

  return (
    <div className="rounded-lg bg-red-50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-900">Tier Distribution</h4>
      <div className="space-y-2">
        {tiers.map((tier) => {
          const { count, percent } = summary.tier_distribution[tier]
          return (
            <div key={tier} className="flex items-center gap-2">
              <div
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: FIRE_TIER_COLORS[tier] }}
              />
              <span className="text-xs text-gray-600 w-16">{tier}</span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.max(percent, 0.5)}%`,
                    backgroundColor: FIRE_TIER_COLORS[tier],
                  }}
                />
              </div>
              <span className="text-xs text-gray-500 w-20 text-right">
                {count.toLocaleString()} ({percent}%)
              </span>
            </div>
          )
        })}
      </div>
      <div className="mt-3 pt-3 border-t border-red-200">
        <div className="text-xs text-gray-500">
          Total Parcels: <span className="font-medium">{total.toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}

/**
 * WUI statistics display
 */
interface WuiStatsProps {
  summary: FireRiskSummary | null
}

function WuiStats({ summary }: WuiStatsProps) {
  if (!summary) return null

  const { parcels_in_wui, percent_in_wui } = summary.wui_statistics
  const { mean, median, min, max } = summary.score_statistics

  return (
    <div className="rounded-lg bg-amber-50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-900">Key Statistics</h4>
      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="text-xs text-gray-500">Parcels in WUI</dt>
          <dd className="text-lg font-semibold text-gray-900">
            {parcels_in_wui.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">% in WUI</dt>
          <dd className="text-lg font-semibold text-amber-600">{percent_in_wui}%</dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Mean Score</dt>
          <dd className="text-lg font-semibold text-gray-900">{mean}</dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Median Score</dt>
          <dd className="text-lg font-semibold text-gray-900">{median}</dd>
        </div>
      </dl>
      <div className="mt-2 text-xs text-gray-500">
        Score Range: {min} - {max}
      </div>
    </div>
  )
}

/**
 * Methodology info
 */
function MethodologyInfo() {
  return (
    <div className="text-xs text-gray-500 space-y-1">
      <p className="font-medium text-gray-700">Component Weights:</p>
      <ul className="space-y-0.5 pl-2">
        <li>
          <span className="font-medium">FHSZ Zone:</span> 35%
        </li>
        <li>
          <span className="font-medium">Slope Risk:</span> 20%
        </li>
        <li>
          <span className="font-medium">WUI Status:</span> 20%
        </li>
        <li>
          <span className="font-medium">Fire History:</span> 15%
        </li>
        <li>
          <span className="font-medium">Vegetation:</span> 10%
        </li>
      </ul>
    </div>
  )
}

/**
 * Main control panel for fire risk layer
 */
export function FireRiskControlPanel() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const layerOpacity = useLayerStore((state) => state.layerOpacity)
  const setLayerOpacity = useLayerStore((state) => state.setLayerOpacity)

  const summary = useFireRiskStore((state) => state.summary)
  const setSummary = useFireRiskStore((state) => state.setSummary)
  const summaryLoading = useFireRiskStore((state) => state.summaryLoading)
  const setSummaryLoading = useFireRiskStore((state) => state.setSummaryLoading)

  const isVisible = visibleLayers.has('fire-risk-index')
  const opacity = layerOpacity['fire-risk-index'] ?? 1

  // Load summary data on mount
  useEffect(() => {
    if (!summary && !summaryLoading) {
      setSummaryLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/fire-risk-index-summary.json`)
        .then((res) => res.json())
        .then((data) => setSummary(data as FireRiskSummary))
        .catch((err) => {
          console.error('Failed to load fire risk summary:', err)
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
      aria-labelledby="fire-risk-control-heading"
      className="border-t border-gray-200"
    >
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 id="fire-risk-control-heading" className="text-base font-semibold text-gray-900">
              Fire Risk Index
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Wildfire risk assessment by parcel
            </p>
          </div>
          <Link
            to="/methodology/fire-risk-index"
            className="text-xs text-primary-600 hover:text-primary-700 hover:underline whitespace-nowrap"
          >
            View Methodology
          </Link>
        </div>
      </div>

      <div className="space-y-5 p-4">
        {/* Layer opacity */}
        <Slider
          label="Layer Opacity"
          value={Math.round(opacity * 100)}
          min={0}
          max={100}
          onChange={(v) => setLayerOpacity('fire-risk-index', v / 100)}
          formatValue={(v) => `${v}%`}
        />

        {/* Legend */}
        <FireRiskLegend />

        {/* Tier distribution */}
        <TierDistribution summary={summary} />

        {/* WUI statistics */}
        <WuiStats summary={summary} />

        {/* Methodology */}
        <MethodologyInfo />
      </div>
    </section>
  )
}
