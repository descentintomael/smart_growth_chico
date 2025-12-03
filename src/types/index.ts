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

export type LayerGroup = 'voting' | 'planning' | 'infrastructure' | 'demographics'

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
