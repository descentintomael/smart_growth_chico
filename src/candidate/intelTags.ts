import type { CatchmentAggregate } from './types'

export type TagCategory = 'political' | 'demographic' | 'economic' | 'lifestyle'

export interface IntelTag {
  label: string
  category: TagCategory
  /** Optional sub-tone: 'd' (Democratic), 'r' (Republican). Used by political tags. */
  tone?: 'd' | 'r' | 'neutral'
}

const pct = (n: number, d: number): number => (d > 0 ? n / d : 0)
const round = (x: number): number => Math.round(x * 100)

/**
 * Computes a punchy 5-8 chip set summarizing what's distinctive about a
 * catchment relative to "typical." Thresholds chosen so most catchments
 * surface 4-7 tags — enough signal without becoming a tag soup.
 */
export function computeIntelTags(c: CatchmentAggregate): IntelTag[] {
  const tags: IntelTag[] = []
  const pop = c.total_population
  if (!pop) return tags

  // ---- Demographic ----
  const seniorShare = pct(c.age_65_plus, pop)
  if (seniorShare >= 0.25) {
    tags.push({ label: `Senior-heavy ${round(seniorShare)}%`, category: 'demographic' })
  }
  const youngShare = pct(c.age_18_34, pop)
  if (youngShare >= 0.32) {
    tags.push({ label: `Young ${round(youngShare)}%`, category: 'demographic' })
  }
  const spanishShare = pct(c.lang_spanish ?? 0, pop)
  if (spanishShare >= 0.10) {
    tags.push({ label: `Spanish-speaking ${round(spanishShare)}%`, category: 'demographic' })
  }
  const eduTotal =
    c.edu_less_than_hs + c.edu_high_school + c.edu_some_college +
    c.edu_bachelors + c.edu_graduate
  const collegeShare = pct(c.edu_bachelors + c.edu_graduate, eduTotal)
  if (collegeShare >= 0.50) {
    tags.push({ label: `Highly educated ${round(collegeShare)}%`, category: 'demographic' })
  }

  // ---- Economic ----
  const incomeTotal =
    c.income_low_under_25k + c.income_lower_mid_25_50k + c.income_mid_50_75k +
    c.income_upper_mid_75_125k + c.income_high_125k_plus
  const lowShare = pct(c.income_low_under_25k + c.income_lower_mid_25_50k, incomeTotal)
  const highShare = pct(c.income_high_125k_plus, incomeTotal)
  if (lowShare >= 0.25 && highShare >= 0.25) {
    tags.push({ label: 'Bimodal income', category: 'economic' })
  } else if (highShare >= 0.35) {
    tags.push({ label: `Affluent ${round(highShare)}% $125k+`, category: 'economic' })
  } else if (lowShare >= 0.40) {
    tags.push({ label: `Low-income ${round(lowShare)}% <$50k`, category: 'economic' })
  }

  const rentBurdenShare = pct(c.rent_burden_30_plus ?? 0, c.rent_burden_total ?? 0)
  if (rentBurdenShare >= 0.45) {
    tags.push({ label: `Rent-burdened ${round(rentBurdenShare)}%`, category: 'economic' })
  }
  const snapShare = pct(c.snap_receiving ?? 0, c.snap_total_households ?? 0)
  if (snapShare >= 0.20) {
    tags.push({ label: `SNAP ${round(snapShare)}% of HH`, category: 'economic' })
  }

  // ---- Political ----
  const reg24Total = c.g24_total_registered ?? 0
  const reg24D = c.g24_reg_democratic ?? 0
  const reg24R = c.g24_reg_republican ?? 0
  if (reg24Total > 0) {
    const lean = (reg24D - reg24R) / reg24Total
    if (lean >= 0.08) {
      tags.push({ label: `D-leaning +${round(lean)}pt`, category: 'political', tone: 'd' })
    } else if (lean <= -0.08) {
      tags.push({ label: `R-leaning +${round(-lean)}pt`, category: 'political', tone: 'r' })
    } else if (Math.abs(lean) <= 0.04) {
      tags.push({ label: 'Competitive', category: 'political', tone: 'neutral' })
    }
  }

  // 2022 → 2024 partisan trend at top of ticket
  const tt24 =
    (c.g24_top_race_democratic ?? 0) + (c.g24_top_race_republican ?? 0) +
    (c.g24_top_race_libertarian ?? 0) + (c.g24_top_race_green ?? 0) +
    (c.g24_top_race_peace_and_freedom ?? 0) + (c.g24_top_race_american_independent ?? 0)
  const tt22 = (c.g22_top_race_democratic ?? 0) + (c.g22_top_race_republican ?? 0)
  if (tt24 > 0 && tt22 > 0) {
    const dShare24 = (c.g24_top_race_democratic ?? 0) / tt24
    const dShare22 = (c.g22_top_race_democratic ?? 0) / tt22
    const shift = dShare24 - dShare22
    if (shift >= 0.03) {
      tags.push({ label: `D-trending +${round(shift)}pt`, category: 'political', tone: 'd' })
    } else if (shift <= -0.03) {
      tags.push({ label: `R-trending +${round(-shift)}pt`, category: 'political', tone: 'r' })
    }
  }

  // Turnout
  const turnout = pct(c.g24_total_votes ?? 0, c.g24_total_registered ?? 0)
  if (turnout >= 0.80) {
    tags.push({ label: `High turnout ${round(turnout)}%`, category: 'political', tone: 'neutral' })
  } else if (turnout > 0 && turnout < 0.55) {
    tags.push({ label: `Low turnout ${round(turnout)}%`, category: 'political', tone: 'neutral' })
  }

  // ---- Lifestyle ----
  const workers = c.commute_total_workers ?? 0
  if (workers > 0) {
    const wfh = pct(c.commute_work_from_home ?? 0, workers)
    if (wfh >= 0.15) {
      tags.push({ label: `Work-from-home ${round(wfh)}%`, category: 'lifestyle' })
    }
    const active = pct(
      (c.commute_public_transit ?? 0) + (c.commute_bicycle ?? 0) + (c.commute_walked ?? 0),
      workers
    )
    if (active >= 0.12) {
      tags.push({ label: `Transit/bike/walk ${round(active)}%`, category: 'lifestyle' })
    }
  }

  const housingTotal =
    (c.housing_single_family ?? 0) + (c.housing_small_multifamily ?? 0) +
    (c.housing_large_multifamily ?? 0) + (c.housing_mobile_home ?? 0)
  const multifam = pct(
    (c.housing_large_multifamily ?? 0) + (c.housing_small_multifamily ?? 0),
    housingTotal
  )
  if (multifam >= 0.35) {
    tags.push({ label: `Multifamily ${round(multifam)}%`, category: 'lifestyle' })
  } else if ((c.housing_single_family ?? 0) / Math.max(housingTotal, 1) >= 0.85) {
    tags.push({ label: 'Single-family belt', category: 'lifestyle' })
  }

  return tags
}

export function tagClasses(t: IntelTag): { wrap: string; dot: string } {
  if (t.category === 'political') {
    if (t.tone === 'd') {
      return { wrap: 'bg-blue-50 text-blue-900 ring-blue-100', dot: 'bg-blue-500' }
    }
    if (t.tone === 'r') {
      return { wrap: 'bg-red-50 text-red-900 ring-red-100', dot: 'bg-red-500' }
    }
    return { wrap: 'bg-slate-100 text-slate-800 ring-slate-200', dot: 'bg-slate-500' }
  }
  if (t.category === 'economic') {
    return { wrap: 'bg-amber-50 text-amber-900 ring-amber-100', dot: 'bg-amber-500' }
  }
  if (t.category === 'demographic') {
    return { wrap: 'bg-emerald-50 text-emerald-900 ring-emerald-100', dot: 'bg-emerald-500' }
  }
  // lifestyle
  return { wrap: 'bg-violet-50 text-violet-900 ring-violet-100', dot: 'bg-violet-500' }
}
