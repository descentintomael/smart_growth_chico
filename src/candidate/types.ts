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
