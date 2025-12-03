import type { FeatureCollection, Feature, Geometry } from 'geojson'

// Layer visibility and configuration types
export interface LayerConfig {
  id: string
  name: string
  description: string
  dataUrl: string
  type: 'polygon' | 'line' | 'point' | 'marker'
  defaultVisible: boolean
  group: LayerGroup
  choropleth?: ChoroplethConfig
  popup?: PopupConfig
  style?: LayerStyle
}

export type LayerGroup = 'voting' | 'planning' | 'infrastructure' | 'demographics' | 'retrofit'

export interface ChoroplethConfig {
  property: string
  scale: string[]
  domain?: [number, number]
  mode: 'quantile' | 'equidistant' | 'jenks'
  steps: number
  legendTitle: string
  formatValue: (v: number) => string
}

export interface PopupConfig {
  title: string
  fields: PopupField[]
}

export interface PopupField {
  label: string
  property: string
  format?: (v: unknown) => string
}

export interface LayerStyle {
  fillColor?: string
  fillOpacity?: number
  color?: string
  weight?: number
  dashArray?: string
}

// Precinct voting data types
export interface PrecinctProperties {
  PRECINCT: string
  COUNTY: string
  percent_yes_o?: number
  percent_no_o?: number
  percent_yes_p?: number
  percent_no_p?: number
  total_votes_o?: number
  total_votes_p?: number
}

export type PrecinctFeature = Feature<Geometry, PrecinctProperties>
export type PrecinctCollection = FeatureCollection<Geometry, PrecinctProperties>

// Opportunity site types
export interface OpportunitySiteProperties {
  site_id: number
  name: string
  type: string
  acres: number
  dist_downtown_mi: number
  predominant_zone: string
  parks_5min: boolean
  parks_10min: boolean
  infra_age: string
  potential_units: number
  priority_score: number
}

export type OpportunitySiteFeature = Feature<Geometry, OpportunitySiteProperties>
export type OpportunitySiteCollection = FeatureCollection<Geometry, OpportunitySiteProperties>

// Council district types
export interface DistrictProperties {
  district_number: number
  name: string
  population?: number
  households?: number
}

export type DistrictFeature = Feature<Geometry, DistrictProperties>
export type DistrictCollection = FeatureCollection<Geometry, DistrictProperties>

// Upzone scenario types
export interface UpzoneParcelProperties {
  APN: string
  cur_zone: string
  upzone_to: string
  cur_tax_acre: number
  proj_tax_acre: number
  delta_tax_acre: number
  delta_tax_total: number
  cur_sg_index: number
  proj_sg_index: number
  delta_sg_index: number
  cur_units: number
  proj_units: number
  delta_units: number
  upzone_elig: 0 | 1
  upzone_tier: 0 | 1 | 2 | 3 | 4
  sc_fiscal: number
  sc_util: number
  sc_infra: number
  sc_zone: number
  sc_loc: number
  Lt_Acre: number
  adoption_priority: number | null
}

export type UpzoneFeature = Feature<Geometry, UpzoneParcelProperties>
export type UpzoneCollection = FeatureCollection<Geometry, UpzoneParcelProperties>

export type UpzoneViewMode = 'current' | 'projected'

export interface AdoptionScenario {
  parcels: number
  acres: number
  tax_increase_annual: number
  new_units: number
  avg_sg_change: number
}

export interface TierSummary {
  description: string
  parcels: number
  acres: number
}

export interface UpzoneSummary {
  generated: string
  description: string
  total_eligible_parcels: number
  total_eligible_acres: number
  current_totals: {
    r1_parcels: number
    r2_parcels: number
    total_current_units: number
    total_current_tax: number
  }
  tier_summary: Record<string, TierSummary>
  tax_medians_per_acre: Record<string, number>
  adoption_scenarios: Record<string, AdoptionScenario>
  max_potential: {
    tax_increase_annual: number
    new_units: number
    avg_sg_index_change: number
  }
}

// Commercial viability site properties (from GeoJSON)
export interface CommercialViabilitySiteProperties {
  site_name: string
  site_acres: number
  cur_pop_qtr: number
  cur_pop_half: number
  cur_pop_1mi: number
  upz_unit_qtr: number
  upz_unit_half: number
  upz_unit_1mi: number
  cur_biz_cnt: number
  biz_100_cnt: number
  new_biz_cnt: number
}

export type CommercialViabilitySiteFeature = Feature<Geometry, CommercialViabilitySiteProperties>
export type CommercialViabilitySiteCollection = FeatureCollection<
  Geometry,
  CommercialViabilitySiteProperties
>

// Commercial viability summary types
export interface CommercialViabilitySummary {
  generated: string
  description: string
  methodology: {
    pph_factor: number
    catchment_distances_ft: Record<string, number>
    source: string
  }
  retail_thresholds: Record<
    string,
    { population: number; catchment: string; label: string }
  >
  total_opportunity_sites: number
  opportunity_sites: CommercialViabilitySite[]
  aggregate_totals: CommercialViabilityAggregate
}

export interface CommercialViabilitySite {
  name: string
  acres: number
  current_population: Record<string, number>
  businesses_currently_viable: string[]
  businesses_current_count: number
  adoption_scenarios: Record<string, CommercialViabilityScenario>
}

export interface CommercialViabilityScenario {
  new_residents: number
  total_population: Record<string, number>
  businesses_viable: string[]
  businesses_viable_count: number
  new_businesses_enabled: string[]
  new_businesses_count: number
}

export interface CommercialViabilityAggregate {
  current: {
    total_population: number
    total_businesses_viable: number
    businesses_by_type: Record<string, number>
  }
  [key: string]:
    | {
        new_residents?: number
        total_businesses_viable?: number
        new_businesses_enabled?: number
        businesses_by_type?: Record<string, number>
        new_businesses_by_type?: Record<string, number>
      }
    | {
        total_population: number
        total_businesses_viable: number
        businesses_by_type: Record<string, number>
      }
}

// Parking Retrofit properties (GeoJSON)
export interface ParkingRetrofitProperties {
  APN: string
  acres: number
  cur_tax: number
  cur_tx_ac: number
  pot_tax: number
  pot_tx_ac: number
  forgn_tax: number
  pot_units: number
  pot_resid: number
}

export type ParkingRetrofitFeature = Feature<Geometry, ParkingRetrofitProperties>
export type ParkingRetrofitCollection = FeatureCollection<Geometry, ParkingRetrofitProperties>

// Vacant Infill properties (GeoJSON)
export interface VacantInfillProperties {
  APN: string
  acres: number
  size_cat: 'small' | 'medium' | 'large'
  Zoning: string
  cur_tax: number
  pot_tax: number
  tax_incr: number
  pot_units: number
  pot_resid: number
}

export type VacantInfillFeature = Feature<Geometry, VacantInfillProperties>
export type VacantInfillCollection = FeatureCollection<Geometry, VacantInfillProperties>

// Commercial Retrofit properties (GeoJSON)
export interface CommercialRetrofitProperties {
  APN: string
  land_use: string
  acres: number
  bldg_cov: number
  imp_ratio: number
  priority: 'high' | 'medium' | 'low'
  cur_tax: number
  pot_tax: number
  tax_incr: number
  pot_units: number
  pot_resid: number
}

export type CommercialRetrofitFeature = Feature<Geometry, CommercialRetrofitProperties>
export type CommercialRetrofitCollection = FeatureCollection<Geometry, CommercialRetrofitProperties>

// Retrofit adoption scenario (shared across scenarios)
export interface RetrofitAdoptionScenario {
  parcels_developed?: number
  parcels_retrofitted?: number
  acres_developed?: number
  acres_retrofitted?: number
  housing_units: number
  new_residents: number
  tax_increase: number
}

// Retrofit summary types
export interface ParkingRetrofitSummary {
  generated: string
  description: string
  case_study_reference: string
  methodology: {
    development_type: string
    units_per_acre: number
    pph_factor: number
    potential_tax_per_acre: number
    source: string
  }
  totals: {
    parking_parcels: number
    total_acres: number
    current_tax_revenue: number
    potential_tax_revenue: number
    forgone_tax_revenue: number
    potential_housing_units: number
    potential_residents: number
  }
  key_metrics: {
    avg_current_tax_per_acre: number
    avg_forgone_tax_per_acre: number
    tax_ratio: number
  }
}

export interface VacantInfillSummary {
  generated: string
  description: string
  case_study_reference: string
  methodology: {
    development_type: string
    units_per_acre: number
    pph_factor: number
    min_parcel_size_acres: number
    potential_tax_per_acre: number
    source: string
  }
  totals: {
    vacant_parcels: number
    buildable_parcels: number
    excluded_parcels: number
    total_acres: number
    current_tax_revenue: number
    potential_tax_revenue: number
    tax_increase: number
    potential_housing_units: number
    potential_residents: number
  }
  by_size_category: Record<
    string,
    {
      count: number
      acres: number
      potential_units: number
      potential_tax_increase: number
      label: string
    }
  >
  adoption_scenarios: Record<string, RetrofitAdoptionScenario>
}

export interface CommercialRetrofitSummary {
  generated: string
  description: string
  case_study_reference: string
  methodology: {
    development_type: string
    units_per_acre: number
    pph_factor: number
    underutilized_threshold_bldg_cov: number
    underutilized_threshold_imp_ratio: number
    potential_tax_per_acre: number
    source: string
  }
  totals: {
    commercial_parcels: number
    underutilized_parcels: number
    commercial_acres: number
    underutilized_acres: number
    current_tax_revenue: number
    potential_tax_revenue: number
    tax_increase: number
    potential_housing_units: number
    potential_residents: number
  }
  by_priority: Record<
    string,
    {
      count: number
      acres: number
      potential_units: number
      potential_tax_increase: number
      avg_bldg_coverage: number
    }
  >
  adoption_scenarios: Record<string, RetrofitAdoptionScenario>
}

// Union type for all retrofit properties
export type RetrofitProperties =
  | ParkingRetrofitProperties
  | VacantInfillProperties
  | CommercialRetrofitProperties

// Retrofit layer IDs
export type RetrofitLayerId = 'parking-retrofit' | 'vacant-infill' | 'commercial-retrofit'
