import { useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useRetrofitStore } from '@/stores/retrofitStore'
import { useLayerStore } from '@/stores/layerStore'
import type {
  RetrofitLayerId,
  ParkingRetrofitSummary,
  VacantInfillSummary,
  CommercialRetrofitSummary,
  RetrofitAdoptionScenario,
} from '@/types'

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
        <span className="text-sm font-semibold text-amber-600">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-amber-600"
        aria-label={label}
      />
    </div>
  )
}

// Interpolate between adoption scenario breakpoints
function interpolateScenario(
  scenarios: Record<string, RetrofitAdoptionScenario>,
  percent: number
): RetrofitAdoptionScenario {
  const breakpoints = [10, 25, 50, 100]

  if (percent <= 0) {
    return { housing_units: 0, new_residents: 0, tax_increase: 0 }
  }

  // Find surrounding breakpoints
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

  // Linear interpolation
  const t = upper === lower ? 1 : (percent - lower) / (upper - lower)

  const lowerData =
    lower === 0
      ? { housing_units: 0, new_residents: 0, tax_increase: 0 }
      : (scenarios[lower.toString()] ?? { housing_units: 0, new_residents: 0, tax_increase: 0 })
  const upperData =
    scenarios[upper.toString()] ?? { housing_units: 0, new_residents: 0, tax_increase: 0 }

  return {
    housing_units: Math.round(
      lowerData.housing_units + t * (upperData.housing_units - lowerData.housing_units)
    ),
    new_residents: Math.round(
      lowerData.new_residents + t * (upperData.new_residents - lowerData.new_residents)
    ),
    tax_increase: Math.round(
      lowerData.tax_increase + t * (upperData.tax_increase - lowerData.tax_increase)
    ),
  }
}

interface SummaryStatsProps {
  layerId: RetrofitLayerId
  adoptionPercent: number
  summary:
    | ParkingRetrofitSummary
    | VacantInfillSummary
    | CommercialRetrofitSummary
    | null
}

function SummaryStats({ layerId, adoptionPercent, summary }: SummaryStatsProps) {
  if (!summary) {
    return (
      <div className="rounded-lg bg-gray-50 p-4">
        <p className="text-sm text-gray-500">Loading summary data...</p>
      </div>
    )
  }

  // Calculate stats based on layer type and adoption
  let units: number
  let residents: number
  let taxIncrease: number
  let parcels: number

  if (layerId === 'parking-retrofit') {
    const parkingSummary = summary as ParkingRetrofitSummary
    units = parkingSummary.totals.potential_housing_units
    residents = parkingSummary.totals.potential_residents
    taxIncrease = parkingSummary.totals.forgone_tax_revenue
    parcels = parkingSummary.totals.parking_parcels
  } else {
    const scenarioSummary = summary as VacantInfillSummary | CommercialRetrofitSummary
    const interpolated = interpolateScenario(
      scenarioSummary.adoption_scenarios,
      adoptionPercent
    )
    units = interpolated.housing_units
    residents = interpolated.new_residents
    taxIncrease = interpolated.tax_increase

    if ('buildable_parcels' in scenarioSummary.totals) {
      parcels = Math.round(
        (scenarioSummary.totals.buildable_parcels * adoptionPercent) / 100
      )
    } else if ('underutilized_parcels' in scenarioSummary.totals) {
      parcels = Math.round(
        (scenarioSummary.totals.underutilized_parcels * adoptionPercent) / 100
      )
    } else {
      parcels = 0
    }
  }

  return (
    <div className="rounded-lg bg-amber-50 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-900">Projected Impact</h4>
      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="text-xs text-gray-500">Housing Units</dt>
          <dd className="text-lg font-semibold text-amber-600">
            +{units.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">New Residents</dt>
          <dd className="text-lg font-semibold text-gray-900">
            +{residents.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">
            {layerId === 'parking-retrofit' ? 'Forgone Tax Revenue' : 'Tax Increase'}
          </dt>
          <dd className="text-lg font-semibold text-amber-600">
            ${taxIncrease.toLocaleString()}/yr
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Parcels</dt>
          <dd className="text-lg font-semibold text-gray-900">{parcels}</dd>
        </div>
      </dl>
    </div>
  )
}

const RETROFIT_LAYERS: RetrofitLayerId[] = [
  'parking-retrofit',
  'vacant-infill',
  'commercial-retrofit',
]

const LAYER_TITLES: Record<RetrofitLayerId, string> = {
  'parking-retrofit': 'Parking Lot Retrofit',
  'vacant-infill': 'Vacant Parcel Infill',
  'commercial-retrofit': 'Commercial Corridor Retrofit',
}

const LAYER_DESCRIPTIONS: Record<RetrofitLayerId, string> = {
  'parking-retrofit':
    'Based on Hartford, CT case study. Converts underutilized parking lots to 3-story mixed-use housing.',
  'vacant-infill':
    'Based on South Bend, IN scattered-site infill program with 75% infrastructure cost savings.',
  'commercial-retrofit':
    'Based on Boston MAPC study showing 125,000 housing units possible from 10% strip mall retrofit.',
}

export function RetrofitControlPanel() {
  const visibleLayers = useLayerStore((state) => state.visibleLayers)
  const layerOpacity = useLayerStore((state) => state.layerOpacity)
  const setLayerOpacity = useLayerStore((state) => state.setLayerOpacity)

  // Get active retrofit layer
  const activeLayer = RETROFIT_LAYERS.find((id) => visibleLayers.has(id))

  // Store state
  const vacantAdoption = useRetrofitStore((state) => state.vacantAdoption)
  const setVacantAdoption = useRetrofitStore((state) => state.setVacantAdoption)
  const commercialAdoption = useRetrofitStore((state) => state.commercialAdoption)
  const setCommercialAdoption = useRetrofitStore((state) => state.setCommercialAdoption)

  const parkingSummary = useRetrofitStore((state) => state.parkingSummary)
  const setParkingSummary = useRetrofitStore((state) => state.setParkingSummary)
  const parkingLoading = useRetrofitStore((state) => state.parkingLoading)
  const setParkingLoading = useRetrofitStore((state) => state.setParkingLoading)

  const vacantSummary = useRetrofitStore((state) => state.vacantSummary)
  const setVacantSummary = useRetrofitStore((state) => state.setVacantSummary)
  const vacantLoading = useRetrofitStore((state) => state.vacantLoading)
  const setVacantLoading = useRetrofitStore((state) => state.setVacantLoading)

  const commercialSummary = useRetrofitStore((state) => state.commercialSummary)
  const setCommercialSummary = useRetrofitStore((state) => state.setCommercialSummary)
  const commercialLoading = useRetrofitStore((state) => state.commercialLoading)
  const setCommercialLoading = useRetrofitStore((state) => state.setCommercialLoading)

  // Load summary data when layer becomes visible
  useEffect(() => {
    if (activeLayer === 'parking-retrofit' && !parkingSummary && !parkingLoading) {
      setParkingLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/parking-retrofit-summary.json`)
        .then((res) => res.json())
        .then((data) => setParkingSummary(data as ParkingRetrofitSummary))
        .catch((err) => {
          console.error('Failed to load parking retrofit summary:', err)
          setParkingLoading(false)
        })
    }
  }, [activeLayer, parkingSummary, parkingLoading, setParkingSummary, setParkingLoading])

  useEffect(() => {
    if (activeLayer === 'vacant-infill' && !vacantSummary && !vacantLoading) {
      setVacantLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/vacant-infill-summary.json`)
        .then((res) => res.json())
        .then((data) => setVacantSummary(data as VacantInfillSummary))
        .catch((err) => {
          console.error('Failed to load vacant infill summary:', err)
          setVacantLoading(false)
        })
    }
  }, [activeLayer, vacantSummary, vacantLoading, setVacantSummary, setVacantLoading])

  useEffect(() => {
    if (activeLayer === 'commercial-retrofit' && !commercialSummary && !commercialLoading) {
      setCommercialLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/commercial-retrofit-summary.json`)
        .then((res) => res.json())
        .then((data) => setCommercialSummary(data as CommercialRetrofitSummary))
        .catch((err) => {
          console.error('Failed to load commercial retrofit summary:', err)
          setCommercialLoading(false)
        })
    }
  }, [
    activeLayer,
    commercialSummary,
    commercialLoading,
    setCommercialSummary,
    setCommercialLoading,
  ])

  // Get current adoption and summary based on active layer
  // NOTE: These useMemo hooks must be BEFORE any early return to satisfy React Rules of Hooks
  const adoptionPercent = useMemo(() => {
    if (activeLayer === 'vacant-infill') return vacantAdoption
    if (activeLayer === 'commercial-retrofit') return commercialAdoption
    return 100
  }, [activeLayer, vacantAdoption, commercialAdoption])

  const setAdoption = useMemo(() => {
    if (activeLayer === 'vacant-infill') return setVacantAdoption
    if (activeLayer === 'commercial-retrofit') return setCommercialAdoption
    return () => {} // No-op for parking-retrofit
  }, [activeLayer, setVacantAdoption, setCommercialAdoption])

  const summary = useMemo(() => {
    if (activeLayer === 'parking-retrofit') return parkingSummary
    if (activeLayer === 'vacant-infill') return vacantSummary
    if (activeLayer === 'commercial-retrofit') return commercialSummary
    return null
  }, [activeLayer, parkingSummary, vacantSummary, commercialSummary])

  // Don't render if no retrofit layer is visible
  if (!activeLayer) {
    return null
  }

  const opacity = layerOpacity[activeLayer] ?? 1

  const hasAdoptionSlider =
    activeLayer === 'vacant-infill' || activeLayer === 'commercial-retrofit'

  return (
    <section
      role="region"
      aria-labelledby="retrofit-control-heading"
      className="border-t border-gray-200"
    >
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 id="retrofit-control-heading" className="text-base font-semibold text-gray-900">
              {LAYER_TITLES[activeLayer]}
            </h3>
            <p className="mt-0.5 text-xs text-gray-500">{LAYER_DESCRIPTIONS[activeLayer]}</p>
          </div>
          <Link
            to={`/methodology/${activeLayer}`}
            className="text-xs text-primary-600 hover:text-primary-700 hover:underline whitespace-nowrap"
          >
            View Methodology
          </Link>
        </div>
      </div>

      <div className="space-y-5 p-4">
        {/* Adoption slider (only for vacant-infill and commercial-retrofit) */}
        {hasAdoptionSlider && (
          <Slider
            label="Adoption Rate"
            value={adoptionPercent}
            min={0}
            max={100}
            step={5}
            onChange={setAdoption}
            formatValue={(v) => `${v}%`}
          />
        )}

        {/* Layer opacity */}
        <Slider
          label="Layer Opacity"
          value={Math.round(opacity * 100)}
          min={0}
          max={100}
          onChange={(v) => setLayerOpacity(activeLayer, v / 100)}
          formatValue={(v) => `${v}%`}
        />

        {/* Summary statistics */}
        <SummaryStats
          layerId={activeLayer}
          adoptionPercent={adoptionPercent}
          summary={summary}
        />
      </div>
    </section>
  )
}
