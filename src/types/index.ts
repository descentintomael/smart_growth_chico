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
