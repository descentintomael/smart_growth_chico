import { useState } from 'react'
import type { CatchmentAggregate, CatchmentDemographics } from './types'

type Profile = 'walk_10' | 'walk_15' | 'bike_10' | 'bike_15'

const PROFILE_LABEL: Record<Profile, string> = {
  walk_10: 'Walk 10',
  walk_15: 'Walk 15',
  bike_10: 'Bike 10',
  bike_15: 'Bike 15',
}

interface DualCountProps {
  label: string
  inDistrict: number
  total: number
  district: string
}

function DualCount({ label, inDistrict, total, district }: DualCountProps) {
  return (
    <div>
      <div className="text-gray-500">{label}</div>
      <div className="font-semibold tabular-nums text-gray-900">
        {inDistrict.toLocaleString()}
        <span className="ml-1 text-[10px] font-normal text-gray-500">in D{district}</span>
      </div>
      <div className="text-[10px] tabular-nums text-gray-400">
        of {total.toLocaleString()} total
      </div>
    </div>
  )
}

interface BarRowProps {
  label: string
  value: number
  total: number
  color?: string
}

function BarRow({ label, value, total, color = '#3b82f6' }: BarRowProps) {
  const pct = total > 0 ? (value / total) * 100 : 0
  return (
    <div className="grid grid-cols-[5.5rem_minmax(0,1fr)_3.5rem] items-center gap-2 text-[11px]">
      <span className="truncate text-gray-600">{label}</span>
      <div className="h-2 rounded-sm bg-gray-100">
        <div
          className="h-full rounded-sm"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-right tabular-nums text-gray-700">
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="mt-3 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
      {children}
    </h4>
  )
}

export function CatchmentDemographicsPanel({
  data,
  venueId,
  district,
}: {
  data: CatchmentDemographics | null
  venueId: string | null
  district: string
}) {
  const [profile, setProfile] = useState<Profile>('walk_15')

  if (!data || !venueId) return null
  const venue = data.venues[venueId]
  if (!venue) return null
  const bands = venue.catchments[profile]
  if (!bands) {
    return (
      <div className="mt-3 rounded-md bg-white/95 p-2 text-xs text-gray-500 ring-1 ring-gray-200">
        No catchment data for {PROFILE_LABEL[profile]}.
      </div>
    )
  }
  // Bar-chart distributions use the in-district slice (that's the audience that
  // can actually vote for the candidate).
  const c: CatchmentAggregate = bands.in_district
  const t: CatchmentAggregate = bands.total

  const totalRace =
    c.race_white_nh + c.race_black_nh + c.race_native_nh + c.race_asian_nh +
    c.race_pacific_nh + c.race_other_nh + c.race_two_or_more_nh + c.race_hispanic
  const totalEdu =
    c.edu_less_than_hs + c.edu_high_school + c.edu_some_college +
    c.edu_bachelors + c.edu_graduate
  const totalIncome =
    c.income_low_under_25k + c.income_lower_mid_25_50k + c.income_mid_50_75k +
    c.income_upper_mid_75_125k + c.income_high_125k_plus
  const totalTenure = c.tenure_owner + c.tenure_renter
  const noInDistrict = c.total_population === 0

  return (
    <div className="mt-3 max-h-[70vh] overflow-y-auto rounded-md bg-white/95 p-3 ring-1 ring-gray-200 backdrop-blur">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] uppercase tracking-wide text-gray-500">
          Catchment audience
        </span>
        <div className="flex gap-0.5 rounded border border-gray-200 p-0.5">
          {(Object.keys(PROFILE_LABEL) as Profile[]).map(p => (
            <button
              key={p}
              onClick={() => setProfile(p)}
              className={`rounded px-1.5 py-0.5 text-[10px] font-medium transition-colors ${
                p === profile
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
              disabled={!venue.catchments[p]}
            >
              {PROFILE_LABEL[p]}
            </button>
          ))}
        </div>
      </div>

      {noInDistrict && (
        <div className="mt-2 rounded bg-red-50 px-2 py-1.5 text-[11px] text-red-800">
          This catchment doesn't reach any residents inside District {district}.
          Useful only for cross-district outreach.
        </div>
      )}

      <div className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1.5 text-xs">
        <DualCount label="Residents" inDistrict={c.total_population} total={t.total_population} district={district} />
        <DualCount label="Est. voters (CVAP)" inDistrict={c.citizen_voting_age_population} total={t.citizen_voting_age_population} district={district} />
        <DualCount label="Households" inDistrict={c.households_total} total={t.households_total} district={district} />
        <div>
          <div className="text-gray-500">Catchment area</div>
          <div className="font-semibold tabular-nums text-gray-900">
            {c.catchment_area_acres.toFixed(0)}
            <span className="ml-1 text-[10px] font-normal text-gray-500">ac in D{district}</span>
          </div>
          <div className="text-[10px] tabular-nums text-gray-400">
            of {t.catchment_area_acres.toFixed(0)} ac total
          </div>
        </div>
      </div>

      <SectionTitle>Age</SectionTitle>
      <div className="mt-1 space-y-0.5">
        <BarRow label="Under 18" value={c.age_under_18} total={c.total_population} color="#94a3b8" />
        <BarRow label="18–34" value={c.age_18_34} total={c.total_population} color="#3b82f6" />
        <BarRow label="35–54" value={c.age_35_54} total={c.total_population} color="#0ea5e9" />
        <BarRow label="55–64" value={c.age_55_64} total={c.total_population} color="#06b6d4" />
        <BarRow label="65+"   value={c.age_65_plus} total={c.total_population} color="#64748b" />
      </div>

      <SectionTitle>Race / ethnicity</SectionTitle>
      <div className="mt-1 space-y-0.5">
        <BarRow label="White (NH)" value={c.race_white_nh} total={totalRace} color="#475569" />
        <BarRow label="Hispanic"   value={c.race_hispanic} total={totalRace} color="#f59e0b" />
        <BarRow label="Asian"      value={c.race_asian_nh} total={totalRace} color="#10b981" />
        <BarRow label="Black"      value={c.race_black_nh} total={totalRace} color="#8b5cf6" />
        <BarRow label="2+ / Other" value={c.race_two_or_more_nh + c.race_other_nh + c.race_native_nh + c.race_pacific_nh} total={totalRace} color="#94a3b8" />
      </div>

      <SectionTitle>Education (25+)</SectionTitle>
      <div className="mt-1 space-y-0.5">
        <BarRow label="< HS"        value={c.edu_less_than_hs} total={totalEdu} color="#94a3b8" />
        <BarRow label="HS / GED"    value={c.edu_high_school} total={totalEdu} color="#64748b" />
        <BarRow label="Some coll."  value={c.edu_some_college} total={totalEdu} color="#0ea5e9" />
        <BarRow label="Bachelor's"  value={c.edu_bachelors} total={totalEdu} color="#3b82f6" />
        <BarRow label="Graduate"    value={c.edu_graduate} total={totalEdu} color="#1d4ed8" />
      </div>

      <SectionTitle>Household income</SectionTitle>
      <div className="mt-1 space-y-0.5">
        <BarRow label="< $25k"    value={c.income_low_under_25k} total={totalIncome} color="#ef4444" />
        <BarRow label="$25–50k"   value={c.income_lower_mid_25_50k} total={totalIncome} color="#f97316" />
        <BarRow label="$50–75k"   value={c.income_mid_50_75k} total={totalIncome} color="#eab308" />
        <BarRow label="$75–125k"  value={c.income_upper_mid_75_125k} total={totalIncome} color="#22c55e" />
        <BarRow label="$125k+"    value={c.income_high_125k_plus} total={totalIncome} color="#16a34a" />
      </div>

      <SectionTitle>Tenure</SectionTitle>
      <div className="mt-1 space-y-0.5">
        <BarRow label="Owner"  value={c.tenure_owner} total={totalTenure} color="#0ea5e9" />
        <BarRow label="Renter" value={c.tenure_renter} total={totalTenure} color="#f97316" />
      </div>

      <div className="mt-3 text-[10px] leading-snug text-gray-500">
        Distributions are for residents <strong>inside District {district}</strong> only
        ({c.bg_intersect_count} block groups areal-weighted from ACS 2023).
        Total counts compare against everyone the venue reaches regardless of district.
        CVAP is estimated from each parent tract's citizen rate × the BG's adult population.
      </div>
    </div>
  )
}
