import { useState } from 'react'
import type { CatchmentAggregate, CatchmentDemographics } from './types'
import { VENUE_BRIEFINGS } from './narratives'
import { computeIntelTags, tagClasses } from './intelTags'

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
  const [detailsOpen, setDetailsOpen] = useState(false)

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

  // Lead-with + intel tags are pinned to walk_15 in-district so the user sees a
  // consistent "headline" view regardless of which profile they've selected
  // for the detail dashboard below. Hand-written entries in narratives.ts take
  // precedence over the auto-generated ones in catchment-demographics.json.
  const override = VENUE_BRIEFINGS[venueId]
  const leadWith = override?.leadWith ?? venue.lead_with ?? null
  const walk15InD = venue.catchments.walk_15?.in_district
  const intelTags = walk15InD ? computeIntelTags(walk15InD) : []

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
    <div className="mt-3 flex min-h-0 flex-1 flex-col overflow-y-auto rounded-md bg-white/95 ring-1 ring-gray-200 backdrop-blur">
      {/* ====== LEAD WITH ====== */}
      {leadWith && (
        <div className="border-b border-gray-100 bg-amber-50/40 px-4 py-3">
          <div className="flex items-baseline gap-2">
            <div className="h-3 w-0.5 rounded-full bg-amber-500" />
            <div className="text-[9px] font-semibold uppercase tracking-[0.12em] text-amber-700">
              Lead with
            </div>
          </div>
          <p className="mt-1.5 text-[12px] leading-relaxed text-amber-950">
            {leadWith}
          </p>
        </div>
      )}

      {/* ====== INTEL TAGS ====== */}
      {intelTags.length > 0 && (
        <div className="border-b border-gray-100 px-4 py-3">
          <div className="text-[9px] font-semibold uppercase tracking-[0.12em] text-gray-400">
            Intel · what's distinctive
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {intelTags.map(tag => {
              const s = tagClasses(tag)
              return (
                <span
                  key={tag.label}
                  className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10.5px] font-medium ring-1 ring-inset ${s.wrap}`}
                >
                  <span className={`inline-block h-1.5 w-1.5 rounded-full ${s.dot}`} />
                  {tag.label}
                </span>
              )
            })}
          </div>
        </div>
      )}

      {/* ====== EXPAND CONTROL ====== */}
      <button
        type="button"
        onClick={() => setDetailsOpen(o => !o)}
        className="flex w-full items-center justify-between border-b border-gray-100 px-4 py-2 text-[10.5px] font-medium text-gray-600 hover:bg-gray-50"
        aria-expanded={detailsOpen}
      >
        <span className="uppercase tracking-[0.1em]">
          {detailsOpen ? 'Hide full demographic dashboard' : 'Open full demographic dashboard'}
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className={`transition-transform duration-150 ${detailsOpen ? 'rotate-180' : ''}`}
        >
          <path d="M3 4.5 L6 7.5 L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      {/* ====== DETAIL DASHBOARD (collapsible) ====== */}
      {!detailsOpen ? null : (
      <div className="p-3">
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

      {/* === Voter registration + election results === */}
      {c.g24_total_registered != null && c.g24_total_registered > 0 && (() => {
        const reg24 = c.g24_total_registered ?? 0
        const reg22 = c.g22_total_registered ?? 0
        const turnout24 = reg24 ? (c.g24_total_votes ?? 0) / reg24 : 0
        const turnout22 = reg22 ? (c.g22_total_votes ?? 0) / reg22 : 0
        const dShare24 = reg24 ? (c.g24_reg_democratic ?? 0) / reg24 : 0
        const dShare22 = reg22 ? (c.g22_reg_democratic ?? 0) / reg22 : 0
        const rShare24 = reg24 ? (c.g24_reg_republican ?? 0) / reg24 : 0
        const rShare22 = reg22 ? (c.g22_reg_republican ?? 0) / reg22 : 0
        const topD24 = c.g24_top_race_democratic ?? 0
        const topR24 = c.g24_top_race_republican ?? 0
        const topD22 = c.g22_top_race_democratic ?? 0
        const topR22 = c.g22_top_race_republican ?? 0
        const topTotal24 = topD24 + topR24 + (c.g24_top_race_libertarian ?? 0) + (c.g24_top_race_green ?? 0) + (c.g24_top_race_peace_and_freedom ?? 0) + (c.g24_top_race_american_independent ?? 0)
        const topTotal22 = topD22 + topR22
        const presDshare = topTotal24 ? topD24 / topTotal24 : 0
        const govDshare = topTotal22 ? topD22 / topTotal22 : 0
        return (
          <>
            <SectionTitle>Registered voters · 2024 vs 2022 trend</SectionTitle>
            <div className="mt-1 grid grid-cols-3 gap-x-2 gap-y-1 text-[11px]">
              <div className="font-medium text-gray-500"></div>
              <div className="text-right font-medium text-gray-500">2022</div>
              <div className="text-right font-medium text-gray-500">2024</div>
              <div className="text-gray-600">Registered</div>
              <div className="text-right tabular-nums">{reg22.toLocaleString()}</div>
              <div className="text-right tabular-nums">{reg24.toLocaleString()}</div>
              <div className="text-gray-600">Turnout</div>
              <div className="text-right tabular-nums">{(turnout22 * 100).toFixed(0)}%</div>
              <div className="text-right tabular-nums">{(turnout24 * 100).toFixed(0)}%</div>
              <div className="text-gray-600">% Democratic</div>
              <div className="text-right tabular-nums">{(dShare22 * 100).toFixed(0)}%</div>
              <div className="text-right tabular-nums">
                {(dShare24 * 100).toFixed(0)}%
                <span className={`ml-1 text-[10px] ${dShare24 > dShare22 ? 'text-blue-600' : 'text-gray-400'}`}>
                  {dShare24 > dShare22 ? '↑' : dShare24 < dShare22 ? '↓' : '→'}
                  {Math.abs(dShare24 - dShare22) > 0.005 ? `${Math.abs((dShare24 - dShare22) * 100).toFixed(1)}pt` : ''}
                </span>
              </div>
              <div className="text-gray-600">% Republican</div>
              <div className="text-right tabular-nums">{(rShare22 * 100).toFixed(0)}%</div>
              <div className="text-right tabular-nums">
                {(rShare24 * 100).toFixed(0)}%
                <span className={`ml-1 text-[10px] ${rShare24 > rShare22 ? 'text-red-600' : 'text-gray-400'}`}>
                  {rShare24 > rShare22 ? '↑' : rShare24 < rShare22 ? '↓' : '→'}
                  {Math.abs(rShare24 - rShare22) > 0.005 ? `${Math.abs((rShare24 - rShare22) * 100).toFixed(1)}pt` : ''}
                </span>
              </div>
            </div>

            <SectionTitle>Top-of-ticket vote · D vs R share</SectionTitle>
            <div className="mt-1 grid grid-cols-3 gap-x-2 gap-y-1 text-[11px]">
              <div className="font-medium text-gray-500"></div>
              <div className="text-right font-medium text-gray-500">2022 (Gov)</div>
              <div className="text-right font-medium text-gray-500">2024 (Pres)</div>
              <div className="text-gray-600">D share</div>
              <div className="text-right tabular-nums">{(govDshare * 100).toFixed(0)}%</div>
              <div className="text-right tabular-nums">
                {(presDshare * 100).toFixed(0)}%
                <span className={`ml-1 text-[10px] ${presDshare > govDshare ? 'text-blue-600' : 'text-gray-400'}`}>
                  {presDshare > govDshare ? '↑' : presDshare < govDshare ? '↓' : '→'}
                  {Math.abs(presDshare - govDshare) > 0.005 ? `${Math.abs((presDshare - govDshare) * 100).toFixed(1)}pt` : ''}
                </span>
              </div>
            </div>

            <SectionTitle>Registration 2024 by party</SectionTitle>
            <div className="mt-1 space-y-0.5">
              <BarRow label="Democratic" value={c.g24_reg_democratic ?? 0} total={reg24} color="#2563eb" />
              <BarRow label="Republican" value={c.g24_reg_republican ?? 0} total={reg24} color="#dc2626" />
              <BarRow label="No party pref" value={c.g24_reg_no_party_preference ?? 0} total={reg24} color="#64748b" />
              <BarRow label="Libertarian" value={c.g24_reg_libertarian ?? 0} total={reg24} color="#f59e0b" />
              <BarRow label="Am. Indep." value={c.g24_reg_american_independent ?? 0} total={reg24} color="#a16207" />
              <BarRow label="Green" value={c.g24_reg_green ?? 0} total={reg24} color="#16a34a" />
              <BarRow label="Peace & Freedom" value={c.g24_reg_peace_and_freedom ?? 0} total={reg24} color="#7c3aed" />
            </div>
          </>
        )
      })()}

      {/* === FEC partisan donations === */}
      {c.fec_total_amount != null && c.fec_total_amount > 0 && (() => {
        const total = c.fec_total_amount
        const dem = c.fec_dem_amount ?? 0
        const rep = c.fec_rep_amount ?? 0
        const lib = c.fec_lib_amount ?? 0
        const grn = c.fec_gre_amount ?? 0
        const ind = c.fec_ind_amount ?? 0
        const other = c.fec_other_amount ?? 0
        // Show partisan-only ratio (excluding "OTHER" = nonpartisan/issue PACs)
        const partisanTotal = dem + rep
        return (
          <>
            <SectionTitle>FEC partisan donations · 2024 cycle</SectionTitle>
            <div className="mt-1 grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
              <div>
                <div className="text-gray-500">Donors</div>
                <div className="font-semibold tabular-nums text-gray-900">
                  {(c.fec_donor_count ?? 0).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-gray-500">Total $</div>
                <div className="font-semibold tabular-nums text-gray-900">
                  ${Math.round(total).toLocaleString()}
                </div>
              </div>
            </div>
            <div className="mt-2 space-y-0.5">
              <BarRow label="Democratic" value={dem} total={total} color="#2563eb" />
              <BarRow label="Republican" value={rep} total={total} color="#dc2626" />
              <BarRow label="Libertarian" value={lib} total={total} color="#f59e0b" />
              <BarRow label="Green" value={grn} total={total} color="#16a34a" />
              <BarRow label="Independent" value={ind} total={total} color="#7c3aed" />
              <BarRow label="PACs / nonpartisan" value={other} total={total} color="#94a3b8" />
            </div>
            {partisanTotal > 0 && (
              <div className="mt-2 rounded bg-gray-50 px-2 py-1.5 text-[10px] text-gray-600">
                Partisan ratio (D vs R, excluding PACs): {' '}
                <strong>D ${Math.round(dem).toLocaleString()}</strong> vs {' '}
                <strong>R ${Math.round(rep).toLocaleString()}</strong>
                {' — '}
                <span style={{ color: dem >= rep ? '#2563eb' : '#dc2626' }}>
                  {Math.round(dem / partisanTotal * 100)}% D
                </span>
              </div>
            )}
          </>
        )
      })()}

      {/* === Occupation === */}
      {c.commute_total_workers != null && c.commute_total_workers > 0 && (() => {
        const occTotal =
          (c.occ_management_business_science_arts ?? 0) +
          (c.occ_service ?? 0) +
          (c.occ_sales_office ?? 0) +
          (c.occ_natural_resources_construction_maintenance ?? 0) +
          (c.occ_production_transportation_material_moving ?? 0)
        return occTotal > 0 ? (
          <>
            <SectionTitle>Occupations (employed 16+)</SectionTitle>
            <div className="mt-1 space-y-0.5">
              <BarRow label="Mgmt/Bus/Sci/Arts" value={c.occ_management_business_science_arts ?? 0} total={occTotal} color="#1e40af" />
              <BarRow label="Service"           value={c.occ_service ?? 0} total={occTotal} color="#0ea5e9" />
              <BarRow label="Sales / office"    value={c.occ_sales_office ?? 0} total={occTotal} color="#10b981" />
              <BarRow label="Construction etc." value={c.occ_natural_resources_construction_maintenance ?? 0} total={occTotal} color="#a16207" />
              <BarRow label="Prod / transport"  value={c.occ_production_transportation_material_moving ?? 0} total={occTotal} color="#7c3aed" />
            </div>
          </>
        ) : null
      })()}

      {/* === Commute mode === */}
      {c.commute_total_workers != null && c.commute_total_workers > 0 && (
        <>
          <SectionTitle>Commute mode</SectionTitle>
          <div className="mt-1 space-y-0.5">
            <BarRow label="Drove alone"   value={c.commute_drove_alone ?? 0} total={c.commute_total_workers} color="#94a3b8" />
            <BarRow label="Carpool"       value={c.commute_carpooled ?? 0} total={c.commute_total_workers} color="#64748b" />
            <BarRow label="Public transit" value={c.commute_public_transit ?? 0} total={c.commute_total_workers} color="#0ea5e9" />
            <BarRow label="Bicycle"       value={c.commute_bicycle ?? 0} total={c.commute_total_workers} color="#16a34a" />
            <BarRow label="Walked"        value={c.commute_walked ?? 0} total={c.commute_total_workers} color="#22c55e" />
            <BarRow label="Work from home" value={c.commute_work_from_home ?? 0} total={c.commute_total_workers} color="#7c3aed" />
          </div>
        </>
      )}

      {/* === Housing structure === */}
      {((c.housing_single_family ?? 0) + (c.housing_small_multifamily ?? 0) + (c.housing_large_multifamily ?? 0) + (c.housing_mobile_home ?? 0)) > 0 && (() => {
        const hTotal = (c.housing_single_family ?? 0) + (c.housing_small_multifamily ?? 0) + (c.housing_large_multifamily ?? 0) + (c.housing_mobile_home ?? 0)
        return (
          <>
            <SectionTitle>Housing structure</SectionTitle>
            <div className="mt-1 space-y-0.5">
              <BarRow label="Single-family"      value={c.housing_single_family ?? 0} total={hTotal} color="#94a3b8" />
              <BarRow label="Small multifamily"  value={c.housing_small_multifamily ?? 0} total={hTotal} color="#3b82f6" />
              <BarRow label="Large multifamily"  value={c.housing_large_multifamily ?? 0} total={hTotal} color="#1d4ed8" />
              <BarRow label="Mobile home"        value={c.housing_mobile_home ?? 0} total={hTotal} color="#a16207" />
            </div>
          </>
        )
      })()}

      {/* === Language at home === */}
      {(c.lang_english_only ?? 0) + (c.lang_spanish ?? 0) + (c.lang_other ?? 0) > 0 && (() => {
        const lTotal =
          (c.lang_english_only ?? 0) + (c.lang_spanish ?? 0) +
          (c.lang_other_indo_european ?? 0) + (c.lang_asian_pacific_islander ?? 0) +
          (c.lang_other ?? 0)
        return (
          <>
            <SectionTitle>Language at home</SectionTitle>
            <div className="mt-1 space-y-0.5">
              <BarRow label="English only"       value={c.lang_english_only ?? 0} total={lTotal} color="#475569" />
              <BarRow label="Spanish"            value={c.lang_spanish ?? 0} total={lTotal} color="#f59e0b" />
              <BarRow label="Other Indo-Euro"    value={c.lang_other_indo_european ?? 0} total={lTotal} color="#8b5cf6" />
              <BarRow label="Asian / Pacific Is" value={c.lang_asian_pacific_islander ?? 0} total={lTotal} color="#10b981" />
              <BarRow label="Other"              value={c.lang_other ?? 0} total={lTotal} color="#94a3b8" />
            </div>
          </>
        )
      })()}

      {/* === Rent burden + SNAP === */}
      {c.rent_burden_total != null && c.rent_burden_total > 0 && (
        <>
          <SectionTitle>Economic stress signals</SectionTitle>
          <div className="mt-1 grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
            <div>
              <div className="text-gray-500">Rent-burdened</div>
              <div className="font-semibold tabular-nums text-gray-900">
                {Math.round(((c.rent_burden_30_plus ?? 0) / c.rent_burden_total) * 100)}%
                <span className="ml-1 text-[10px] font-normal text-gray-400">of renters {">"}30% income</span>
              </div>
            </div>
            <div>
              <div className="text-gray-500">Severely</div>
              <div className="font-semibold tabular-nums text-gray-900">
                {Math.round(((c.rent_burden_50_plus ?? 0) / c.rent_burden_total) * 100)}%
                <span className="ml-1 text-[10px] font-normal text-gray-400">{">"} 50% income</span>
              </div>
            </div>
            {c.snap_total_households != null && c.snap_total_households > 0 && (
              <div>
                <div className="text-gray-500">SNAP receiving</div>
                <div className="font-semibold tabular-nums text-gray-900">
                  {Math.round(((c.snap_receiving ?? 0) / c.snap_total_households) * 100)}%
                  <span className="ml-1 text-[10px] font-normal text-gray-400">of households</span>
                </div>
              </div>
            )}
            {c.employment_unemployed != null && (c.employment_employed ?? 0) + c.employment_unemployed > 0 && (
              <div>
                <div className="text-gray-500">Unemployment</div>
                <div className="font-semibold tabular-nums text-gray-900">
                  {Math.round((c.employment_unemployed / ((c.employment_employed ?? 0) + c.employment_unemployed)) * 100)}%
                </div>
              </div>
            )}
          </div>
        </>
      )}

      <div className="mt-3 text-[10px] leading-snug text-gray-500">
        Distributions are for residents <strong>inside District {district}</strong> only
        ({c.bg_intersect_count} block groups{c.g24_precinct_intersect_count ? ` + ${c.g24_precinct_intersect_count} 2024 precincts` : ''}{c.fec_zcta_intersect_count ? ` + ${c.fec_zcta_intersect_count} ZIPs` : ''} areal-weighted).
        Total counts compare against everyone the venue reaches regardless of district.
        Sources: ACS 5-year 2023; SWDB Butte 2022+2024 General; FEC 2024 cycle.
      </div>
      </div>
      )}
    </div>
  )
}
