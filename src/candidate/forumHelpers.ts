import type {
  CatchmentAggregate,
  CatchmentBands,
  CatchmentDemographics,
  VenueCollection,
  VenueFeature,
} from './types'

/** Parse a slug like "4-6" or "2-4-6" into ["4", "6"] or ["2","4","6"]. */
export function parseForumSlug(slug: string | undefined): string[] | null {
  if (!slug) return null
  if (!/^\d+(?:-\d+)+$/.test(slug)) return null
  const parts = Array.from(new Set(slug.split('-')))
  parts.sort((a, b) => Number(a) - Number(b))
  return parts
}

const ZERO_AGGREGATE: CatchmentAggregate = {
  total_population: 0,
  adult_population_18plus: 0,
  citizen_voting_age_population: 0,
  age_under_18: 0, age_18_34: 0, age_35_54: 0, age_55_64: 0, age_65_plus: 0,
  race_white_nh: 0, race_black_nh: 0, race_native_nh: 0, race_asian_nh: 0,
  race_pacific_nh: 0, race_other_nh: 0, race_two_or_more_nh: 0, race_hispanic: 0,
  edu_less_than_hs: 0, edu_high_school: 0, edu_some_college: 0,
  edu_bachelors: 0, edu_graduate: 0,
  income_low_under_25k: 0, income_lower_mid_25_50k: 0, income_mid_50_75k: 0,
  income_upper_mid_75_125k: 0, income_high_125k_plus: 0,
  households_total: 0,
  tenure_owner: 0, tenure_renter: 0,
  catchment_area_acres: 0,
  bg_intersect_count: 0,
}

function addAggregates(a: CatchmentAggregate, b: CatchmentAggregate): CatchmentAggregate {
  const result = { ...ZERO_AGGREGATE }
  for (const k of Object.keys(result) as Array<keyof CatchmentAggregate>) {
    result[k] = a[k] + b[k]
  }
  return result
}

export type Profile = 'walk_10' | 'walk_15' | 'bike_10' | 'bike_15'

/** Per-venue, per-profile per-district in-district stats. */
export interface VenueForumStats {
  venue: VenueFeature
  perDistrict: Record<string, Partial<Record<Profile, CatchmentBands>>>
  /** Sum across selected districts (geographically disjoint, so just addition). */
  unionInDistrict: Partial<Record<Profile, CatchmentAggregate>>
  /** Same total polygon catchment regardless of district — pulled from whichever
   *  district happens to have it. */
  total: Partial<Record<Profile, CatchmentAggregate>>
}

/**
 * Merge venues and their catchment demographics across multiple districts,
 * deduplicated by osm_id. For each venue we record:
 *   - per-district in-district stats per profile
 *   - union in-district stats per profile (sum across districts)
 *   - total catchment stats per profile (same regardless of district)
 */
export function mergeForumData(
  perDistrict: Record<string, { venues: VenueCollection; demo: CatchmentDemographics }>
): Map<string, VenueForumStats> {
  const merged = new Map<string, VenueForumStats>()

  for (const [district, data] of Object.entries(perDistrict)) {
    for (const venue of data.venues.features) {
      const id = venue.properties.osm_id
      const demoEntry = data.demo.venues[id]
      if (!merged.has(id)) {
        merged.set(id, {
          venue,
          perDistrict: {},
          unionInDistrict: {},
          total: {},
        })
      }
      const entry = merged.get(id)!
      if (demoEntry) {
        entry.perDistrict[district] = demoEntry.catchments
        for (const [profile, bands] of Object.entries(demoEntry.catchments) as Array<[Profile, CatchmentBands]>) {
          if (!bands) continue
          // Sum in_district across districts
          const current = entry.unionInDistrict[profile] ?? ZERO_AGGREGATE
          entry.unionInDistrict[profile] = addAggregates(current, bands.in_district)
          // Total is identical across districts (catchment polygon doesn't change)
          if (!entry.total[profile]) {
            entry.total[profile] = bands.total
          }
        }
      }
    }
  }
  return merged
}

const WEIGHT_AUDIENCE = 0.40
const WEIGHT_CONFIDENCE = 0.25
const WEIGHT_FIT = 0.25
const WEIGHT_LEGITIMACY = 0.10

function audienceScore(cvap: number): number {
  if (cvap <= 0) return 0
  return Math.min(Math.log10(cvap + 10) / 4.0, 1.0)
}

/**
 * Re-score every venue for a forum view. The audience component uses the
 * GEOMETRIC MEAN of per-district CVAPs (not the sum), because a venue that
 * reaches 0 voters in one district is a poor forum host even if its total
 * audience is large — the candidate from that district gains nothing.
 *
 * Geomean has the property that any zero collapses it to zero, and balanced
 * distributions score higher than skewed distributions with the same sum.
 *   [0, 1341]  → geomean 0  → low audience score
 *   [600, 800] → geomean ~693 → much higher audience score
 *
 * The union sum is still recorded in priority_components.in_district_walk_15_cvap
 * for display, so the user sees total reach + the score reflects balance.
 */
export function rescoreVenuesForForum(
  merged: Map<string, VenueForumStats>,
  selectedDistricts: string[],
): VenueFeature[] {
  const rescored: VenueFeature[] = []
  for (const stats of merged.values()) {
    const venue = stats.venue
    const components = venue.properties.priority_components
    if (!components) continue

    // Per-district walk-15 CVAPs across ALL selected districts. A district missing
    // from stats.perDistrict means the venue's data wasn't in that district's
    // catchment file, so its reach there is effectively 0.
    const perDistrictCvaps = selectedDistricts.map(d =>
      stats.perDistrict[d]?.walk_15?.in_district?.citizen_voting_age_population ?? 0
    )

    const product = perDistrictCvaps.reduce((p, v) => p * Math.max(v, 0), 1)
    const geomean = perDistrictCvaps.length > 0
      ? Math.pow(product, 1 / perDistrictCvaps.length)
      : 0

    const unionCvap = perDistrictCvaps.reduce((a, b) => a + b, 0)
    const totalPop15 = stats.unionInDistrict.walk_15?.total_population ?? 0

    // Coverage ratio = fraction of selected districts where the venue actually
    // reaches voters. A 1-of-2 venue (like Lakeside in D4+D6) is half-useful
    // for a shared forum no matter how good its other characteristics are.
    // Any positive reach counts — the geomean already penalizes very low reach.
    const districtsWithReach = perDistrictCvaps.filter(v => v > 0).length
    const coverageRatio = selectedDistricts.length > 0
      ? districtsWithReach / selectedDistricts.length
      : 1.0

    const newAudience = audienceScore(geomean)
    let composite =
      WEIGHT_AUDIENCE * newAudience
      + WEIGHT_CONFIDENCE * components.confidence
      + WEIGHT_FIT * components.fit
      + WEIGHT_LEGITIMACY * components.legitimacy
    composite = Math.min(composite + components.public_facility_bonus, 1.0)
    // Multiplicative coverage penalty: 1.0 for full coverage, 0.5 for 1-of-2,
    // 0.33 for 1-of-3, etc. Floored at 0.15 so non-reach venues remain visible
    // (just clearly de-prioritized).
    composite *= Math.max(coverageRatio, 0.15)
    if (totalPop15 === 0) composite *= 0.3

    const newVenue: VenueFeature = {
      ...venue,
      properties: {
        ...venue.properties,
        priority_score: Math.round(composite * 10000) / 10000,
        priority_tier: composite >= 0.75 ? 'top' : composite >= 0.55 ? 'high' : composite >= 0.35 ? 'medium' : 'low',
        priority_components: {
          ...components,
          audience: Math.round(newAudience * 1000) / 1000,
          in_district_walk_15_cvap: unionCvap,
        },
        forum_coverage_ratio: coverageRatio,
        forum_districts_with_reach: districtsWithReach,
        forum_districts_total: selectedDistricts.length,
      },
    }
    rescored.push(newVenue)
  }
  rescored.sort((a, b) => (b.properties.priority_score ?? 0) - (a.properties.priority_score ?? 0))
  rescored.forEach((v, i) => {
    v.properties.priority_rank = i + 1
  })
  return rescored
}

/** Build a district-color palette so each boundary in the forum view stands out. */
export const FORUM_DISTRICT_COLORS = ['#2563eb', '#dc2626', '#16a34a', '#f59e0b', '#7c3aed'] as const

export function colorForDistrict(district: string, allDistricts: string[]): string {
  const idx = allDistricts.indexOf(district)
  const i = idx >= 0 ? idx % FORUM_DISTRICT_COLORS.length : 0
  return FORUM_DISTRICT_COLORS[i] as string
}
