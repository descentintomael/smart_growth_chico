import type { Feature, FeatureCollection, Point, Polygon, MultiPolygon } from 'geojson'

export interface VenueProperties {
  osm_id: string
  name: string
  category: string
  amenity: string | null
  leisure: string | null
  tourism?: string | null
  shop?: string | null
  craft?: string | null
  office?: string | null
  club?: string | null
  address: string | null
  website: string | null
  phone: string | null
  capacity: string | null
  wheelchair: string | null
  operator: string | null
  hosting_status: 'confirmed' | 'likely' | 'needs_verification' | 'excluded'
  assessment_confidence?: 'high' | 'medium' | 'low' | 'unknown'
  notes: string | null
  // Priority scoring (added by scripts/score-venue-priority.py)
  priority_score?: number
  priority_tier?: 'top' | 'high' | 'medium' | 'low'
  priority_rank?: number
  priority_components?: {
    audience: number
    confidence: number
    fit: number
    legitimacy: number
    public_facility_bonus: number
    in_district_walk_15_cvap: number
  }
  /** Forum view only: how many of the selected districts have positive reach. */
  forum_coverage_ratio?: number
  forum_districts_with_reach?: number
  forum_districts_total?: number
  /** True when the venue point is inside the district polygon; false if in the adjacency buffer. */
  in_district: boolean
  // Google Places enrichment (optional — venue may not have been enriched yet)
  google_place_id?: string | null
  google_types?: string[]
  google_primary_type?: string | null
  google_business_status?: 'OPERATIONAL' | 'CLOSED_TEMPORARILY' | 'CLOSED_PERMANENTLY' | null
  google_rating?: number | null
  google_user_ratings_count?: number | null
  google_editorial_summary?: string | null
  google_formatted_address?: string | null
}

export type VenueFeature = Feature<Point, VenueProperties>
export type VenueCollection = FeatureCollection<Point, VenueProperties>

export interface DistrictBoundaryProperties {
  DISTRICT: string
  NAME: string
}

export type DistrictBoundaryCollection = FeatureCollection<
  Polygon | MultiPolygon,
  DistrictBoundaryProperties
>

export type CatchmentProfile =
  | 'walk_10'
  | 'walk_15'
  | 'bike_10'
  | 'bike_15'
  // Shell profiles — the ring between consecutive isochrones, no overlap.
  | 'walk_15_only'
  | 'bike_10_only'
  | 'bike_15_only'

export interface CatchmentProperties {
  venue_id: string
  venue_name: string
  profile: CatchmentProfile
  /** "full" = the cumulative isochrone polygon. "shell" = the ring between this band
   *  and the previous one. UI renders shells; demographics aggregation uses fulls. */
  feature_type: 'full' | 'shell'
  mode: 'walk' | 'bike'
  minutes: 10 | 15
  in_district_venue: boolean
}

export type CatchmentCollection = FeatureCollection<
  Polygon | MultiPolygon,
  CatchmentProperties
>

export interface CatchmentAggregate {
  total_population: number
  adult_population_18plus: number
  citizen_voting_age_population: number
  age_under_18: number
  age_18_34: number
  age_35_54: number
  age_55_64: number
  age_65_plus: number
  race_white_nh: number
  race_black_nh: number
  race_native_nh: number
  race_asian_nh: number
  race_pacific_nh: number
  race_other_nh: number
  race_two_or_more_nh: number
  race_hispanic: number
  edu_less_than_hs: number
  edu_high_school: number
  edu_some_college: number
  edu_bachelors: number
  edu_graduate: number
  income_low_under_25k: number
  income_lower_mid_25_50k: number
  income_mid_50_75k: number
  income_upper_mid_75_125k: number
  income_high_125k_plus: number
  households_total: number
  tenure_owner: number
  tenure_renter: number
  catchment_area_acres: number
  bg_intersect_count: number
}

export interface CatchmentBands {
  total: CatchmentAggregate
  in_district: CatchmentAggregate
}

export interface CatchmentDemographics {
  generated: string
  district: number
  data_source_note: string
  venues: Record<string, {
    venue_name: string
    in_district_venue: boolean
    catchments: Partial<Record<'walk_10' | 'walk_15' | 'bike_10' | 'bike_15', CatchmentBands>>
  }>
}
