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
