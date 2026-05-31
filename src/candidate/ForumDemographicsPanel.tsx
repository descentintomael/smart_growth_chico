import { useState } from 'react'
import { colorForDistrict, type Profile, type VenueForumStats } from './forumHelpers'

const PROFILE_LABEL: Record<Profile, string> = {
  walk_10: 'Walk 10',
  walk_15: 'Walk 15',
  bike_10: 'Bike 10',
  bike_15: 'Bike 15',
}

function pct(value: number, total: number): number {
  return total > 0 ? (value / total) * 100 : 0
}

function BarRow({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const p = pct(value, total)
  return (
    <div className="grid grid-cols-[5.5rem_minmax(0,1fr)_3.5rem] items-center gap-2 text-[11px]">
      <span className="truncate text-gray-600">{label}</span>
      <div className="h-2 rounded-sm bg-gray-100">
        <div className="h-full rounded-sm" style={{ width: `${Math.min(p, 100)}%`, backgroundColor: color }} />
      </div>
      <span className="text-right tabular-nums text-gray-700">{p.toFixed(0)}%</span>
    </div>
  )
}

export function ForumDemographicsPanel({
  stats,
  districts,
}: {
  stats: VenueForumStats | undefined
  districts: string[]
}) {
  const [profile, setProfile] = useState<Profile>('walk_15')

  if (!stats) return null
  const union = stats.unionInDistrict[profile]
  const total = stats.total[profile]
  if (!union || !total) {
    return (
      <div className="mt-3 rounded-md bg-white/95 p-2 text-xs text-gray-500 ring-1 ring-gray-200">
        No catchment data for {PROFILE_LABEL[profile]}.
      </div>
    )
  }

  // Per-district in-district values for the selected profile
  const perDistrict = districts.map(d => ({
    district: d,
    color: colorForDistrict(d, districts),
    agg: stats.perDistrict[d]?.[profile]?.in_district,
  }))
  const sumUnionPop = union.total_population
  const sumUnionCvap = union.citizen_voting_age_population

  const totalRace =
    union.race_white_nh + union.race_black_nh + union.race_native_nh + union.race_asian_nh +
    union.race_pacific_nh + union.race_other_nh + union.race_two_or_more_nh + union.race_hispanic
  const totalTenure = union.tenure_owner + union.tenure_renter
  const totalIncome =
    union.income_low_under_25k + union.income_lower_mid_25_50k + union.income_mid_50_75k +
    union.income_upper_mid_75_125k + union.income_high_125k_plus

  return (
    <div className="mt-3 flex min-h-0 flex-1 flex-col overflow-y-auto rounded-md bg-white/95 p-3 ring-1 ring-gray-200 backdrop-blur">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] uppercase tracking-wide text-gray-500">
          Forum audience
        </span>
        <div className="flex gap-0.5 rounded border border-gray-200 p-0.5">
          {(Object.keys(PROFILE_LABEL) as Profile[]).map(p => (
            <button
              key={p}
              onClick={() => setProfile(p)}
              className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                p === profile ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {PROFILE_LABEL[p]}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 text-xs">
        <div>
          <div className="text-gray-500">Total union residents</div>
          <div className="font-semibold tabular-nums text-gray-900">
            {sumUnionPop.toLocaleString()}
          </div>
          <div className="text-[10px] text-gray-400">of {total.total_population.toLocaleString()} in catchment</div>
        </div>
        <div>
          <div className="text-gray-500">Est. voters (CVAP)</div>
          <div className="font-semibold tabular-nums text-gray-900">
            {sumUnionCvap.toLocaleString()}
          </div>
          <div className="text-[10px] text-gray-400">of {total.citizen_voting_age_population.toLocaleString()} total</div>
        </div>
      </div>

      <h4 className="mt-3 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
        Per-district breakdown
      </h4>
      <div className="mt-1 space-y-1">
        {perDistrict.map(({ district, color, agg }) => {
          const v = agg?.total_population ?? 0
          const c = agg?.citizen_voting_age_population ?? 0
          return (
            <div key={district} className="rounded bg-gray-50 px-2 py-1.5 text-[11px]">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: color }} />
                  <span className="font-medium text-gray-700">District {district}</span>
                </span>
                <span className="tabular-nums text-gray-600">
                  {v.toLocaleString()} <span className="text-gray-400">res</span> · {c.toLocaleString()} <span className="text-gray-400">CVAP</span>
                </span>
              </div>
              {sumUnionPop > 0 && (
                <div className="mt-1 h-1.5 rounded-sm bg-gray-200">
                  <div
                    className="h-full rounded-sm"
                    style={{ width: `${pct(v, sumUnionPop)}%`, backgroundColor: color }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>

      <h4 className="mt-3 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
        Union audience demographics
      </h4>
      <div className="mt-1 space-y-0.5">
        <BarRow label="Under 18" value={union.age_under_18} total={sumUnionPop} color="#94a3b8" />
        <BarRow label="18–34"    value={union.age_18_34}   total={sumUnionPop} color="#3b82f6" />
        <BarRow label="35–54"    value={union.age_35_54}   total={sumUnionPop} color="#0ea5e9" />
        <BarRow label="55–64"    value={union.age_55_64}   total={sumUnionPop} color="#06b6d4" />
        <BarRow label="65+"      value={union.age_65_plus} total={sumUnionPop} color="#64748b" />
      </div>
      <h4 className="mt-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500">Race / ethnicity</h4>
      <div className="mt-1 space-y-0.5">
        <BarRow label="White (NH)" value={union.race_white_nh} total={totalRace} color="#475569" />
        <BarRow label="Hispanic"   value={union.race_hispanic} total={totalRace} color="#f59e0b" />
        <BarRow label="Asian"      value={union.race_asian_nh} total={totalRace} color="#10b981" />
        <BarRow label="Black"      value={union.race_black_nh} total={totalRace} color="#8b5cf6" />
        <BarRow
          label="2+ / Other"
          value={union.race_two_or_more_nh + union.race_other_nh + union.race_native_nh + union.race_pacific_nh}
          total={totalRace}
          color="#94a3b8"
        />
      </div>
      <h4 className="mt-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500">Tenure</h4>
      <div className="mt-1 space-y-0.5">
        <BarRow label="Owner"  value={union.tenure_owner}  total={totalTenure} color="#0ea5e9" />
        <BarRow label="Renter" value={union.tenure_renter} total={totalTenure} color="#f97316" />
      </div>
      <h4 className="mt-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500">Income</h4>
      <div className="mt-1 space-y-0.5">
        <BarRow label="< $25k"    value={union.income_low_under_25k}      total={totalIncome} color="#ef4444" />
        <BarRow label="$25–50k"   value={union.income_lower_mid_25_50k}   total={totalIncome} color="#f97316" />
        <BarRow label="$50–75k"   value={union.income_mid_50_75k}         total={totalIncome} color="#eab308" />
        <BarRow label="$75–125k"  value={union.income_upper_mid_75_125k}  total={totalIncome} color="#22c55e" />
        <BarRow label="$125k+"    value={union.income_high_125k_plus}     total={totalIncome} color="#16a34a" />
      </div>
    </div>
  )
}
