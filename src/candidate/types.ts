import type { Feature, FeatureCollection, Point, Polygon, MultiPolygon } from 'geojson'

export interface VenueProperties {
  osm_id: string
  name: string
  category: string
  amenity: string | null
  leisure: string | null
  address: string | null
  website: string | null
  phone: string | null
  capacity: string | null
  wheelchair: string | null
  operator: string | null
  hosting_status: 'confirmed' | 'likely' | 'needs_verification' | 'excluded'
  notes: string | null
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
