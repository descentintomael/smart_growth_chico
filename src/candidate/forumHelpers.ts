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
 * Re-score every venue using the UNION audience (sum of in-district CVAPs across
 * selected districts). Returns the rescored venue features, sorted by score desc.
 */
export function rescoreVenuesForForum(
  merged: Map<string, VenueForumStats>
): VenueFeature[] {
  const rescored: VenueFeature[] = []
  for (const stats of merged.values()) {
    const venue = stats.venue
    const unionCvap = stats.unionInDistrict.walk_15?.citizen_voting_age_population ?? 0
    const totalPop15 = stats.unionInDistrict.walk_15?.total_population ?? 0
    const components = venue.properties.priority_components
    if (!components) continue
    const newAudience = audienceScore(unionCvap)
    let composite =
      WEIGHT_AUDIENCE * newAudience
      + WEIGHT_CONFIDENCE * components.confidence
      + WEIGHT_FIT * components.fit
      + WEIGHT_LEGITIMACY * components.legitimacy
    composite = Math.min(composite + components.public_facility_bonus, 1.0)
    if (totalPop15 === 0) composite *= 0.3
    // Build a new feature with updated priority fields
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
