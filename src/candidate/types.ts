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
  // === New extended demographic + political fields (added 2026-05-31) ===
  // All optional so older catchment-demographics files still type-check.
  // === 2024 General (g24) — Presidential year ===
  g24_precinct_intersect_count?: number
  g24_total_registered?: number
  g24_total_votes?: number
  g24_reg_democratic?: number
  g24_reg_republican?: number
  g24_reg_no_party_preference?: number
  g24_reg_american_independent?: number
  g24_reg_libertarian?: number
  g24_reg_green?: number
  g24_reg_peace_and_freedom?: number
  g24_reg_other?: number
  // Top of ticket = Presidential
  g24_top_race_democratic?: number
  g24_top_race_republican?: number
  g24_top_race_libertarian?: number
  g24_top_race_green?: number
  g24_top_race_peace_and_freedom?: number
  g24_top_race_american_independent?: number
  g24_sen_democratic?: number
  g24_sen_republican?: number
  // === 2022 General (g22) — Midterm with Governor at top of ticket ===
  g22_precinct_intersect_count?: number
  g22_total_registered?: number
  g22_total_votes?: number
  g22_reg_democratic?: number
  g22_reg_republican?: number
  g22_reg_no_party_preference?: number
  g22_reg_american_independent?: number
  g22_reg_libertarian?: number
  g22_reg_green?: number
  g22_reg_peace_and_freedom?: number
  g22_reg_other?: number
  // Top of ticket = Governor (Newsom vs Dahle)
  g22_top_race_democratic?: number
  g22_top_race_republican?: number
  g22_sen_democratic?: number
  g22_sen_republican?: number
  // === FEC partisan donations (2024 cycle, areal-weighted from ZCTAs) ===
  fec_zcta_intersect_count?: number
  fec_donor_count?: number
  fec_total_amount?: number
  fec_dem_amount?: number
  fec_rep_amount?: number
  fec_lib_amount?: number
  fec_gre_amount?: number
  fec_ind_amount?: number
  fec_other_amount?: number
  fec_dem_donor_count?: number
  fec_rep_donor_count?: number
  fec_lib_donor_count?: number
  fec_gre_donor_count?: number
  fec_ind_donor_count?: number
  fec_other_donor_count?: number
  // Commute mode (BG → catchment, areal-weighted)
  commute_total_workers?: number
  commute_drove_alone?: number
  commute_carpooled?: number
  commute_public_transit?: number
  commute_bicycle?: number
  commute_walked?: number
  commute_work_from_home?: number
  // Housing structure
  housing_single_family?: number
  housing_small_multifamily?: number
  housing_large_multifamily?: number
  housing_mobile_home?: number
  // Employment status
  employment_employed?: number
  employment_unemployed?: number
  employment_not_in_labor_force?: number
  // School enrollment
  school_k12?: number
  school_college_undergrad?: number
  school_graduate_professional?: number
  school_not_enrolled?: number
  // SNAP / rent burden / mobility
  snap_receiving?: number
  snap_total_households?: number
  rent_burden_30_plus?: number
  rent_burden_50_plus?: number
  rent_burden_total?: number
  mobility_same_house?: number
  mobility_moved_within_county?: number
  mobility_moved_within_state?: number
  mobility_moved_from_other_state?: number
  mobility_moved_from_abroad?: number
  // Language at home
  lang_english_only?: number
  lang_spanish?: number
  lang_other_indo_european?: number
  lang_asian_pacific_islander?: number
  lang_other?: number
  // Occupation
  occ_management_business_science_arts?: number
  occ_service?: number
  occ_sales_office?: number
  occ_natural_resources_construction_maintenance?: number
  occ_production_transportation_material_moving?: number
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
    /** Auto-generated narrative paragraph from scripts/generate-venue-narratives.py.
     *  Only present for top-50 venues per district with non-trivial in-district
     *  walk-15 catchment. Currently not rendered (briefing was cut from the UI). */
    narrative?: string
    /** Auto-generated "Lead with" tactical paragraph for the candidate. */
    lead_with?: string
    catchments: Partial<Record<'walk_10' | 'walk_15' | 'bike_10' | 'bike_15', CatchmentBands>>
  }>
}
