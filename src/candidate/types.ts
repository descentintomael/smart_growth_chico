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
