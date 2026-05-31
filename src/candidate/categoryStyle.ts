import type { VenueProperties } from './types'

interface CategoryStyle {
  color: string
  label: string
}

const STYLES: Record<string, CategoryStyle> = {
  // Amenity-based
  library: { color: '#1f77b4', label: 'Library' },
  community_centre: { color: '#2ca02c', label: 'Community center' },
  social_centre: { color: '#2ca02c', label: 'Social center' },
  social_facility: { color: '#17becf', label: 'Social facility' },
  events_venue: { color: '#9467bd', label: 'Events venue' },
  conference_centre: { color: '#9467bd', label: 'Conference center' },
  theatre: { color: '#9467bd', label: 'Theatre' },
  cinema: { color: '#9467bd', label: 'Cinema' },
  arts_centre: { color: '#9467bd', label: 'Arts center' },
  music_venue: { color: '#9467bd', label: 'Music venue' },
  nightclub: { color: '#9467bd', label: 'Nightclub' },
  casino: { color: '#9467bd', label: 'Casino' },
  marketplace: { color: '#2ca02c', label: 'Marketplace' },
  clubhouse: { color: '#8c564b', label: 'Clubhouse' },
  college: { color: '#8c564b', label: 'College' },
  university: { color: '#8c564b', label: 'University' },
  school: { color: '#bcbd22', label: 'School' },
  cafe: { color: '#ff7f0e', label: 'Cafe' },
  bar: { color: '#d62728', label: 'Bar' },
  pub: { color: '#d62728', label: 'Pub' },
  biergarten: { color: '#d62728', label: 'Biergarten' },
  restaurant: { color: '#e377c2', label: 'Restaurant' },
  townhall: { color: '#7f7f7f', label: 'Town hall' },
  // Leisure-based (no prefix)
  sports_centre: { color: '#aec7e8', label: 'Sports center' },
  golf_course: { color: '#2ca02c', label: 'Golf course / country club' },
  fitness_centre: { color: '#aec7e8', label: 'Fitness center' },
  dance: { color: '#9467bd', label: 'Dance studio' },
  bowling_alley: { color: '#9467bd', label: 'Bowling alley' },
  recreation_ground: { color: '#aec7e8', label: 'Recreation ground' },
  // Tourism (prefixed)
  tourism_hotel: { color: '#1f77b4', label: 'Hotel' },
  tourism_motel: { color: '#1f77b4', label: 'Motel' },
  tourism_gallery: { color: '#9467bd', label: 'Gallery' },
  tourism_museum: { color: '#9467bd', label: 'Museum' },
  // Shop (prefixed)
  shop_books: { color: '#ff7f0e', label: 'Bookstore' },
  shop_alcohol: { color: '#d62728', label: 'Alcohol retailer' },
  shop_wine: { color: '#d62728', label: 'Wine shop' },
  // Craft (prefixed)
  craft_brewery: { color: '#d62728', label: 'Brewery' },
  craft_winery: { color: '#d62728', label: 'Winery' },
  craft_distillery: { color: '#d62728', label: 'Distillery' },
  // Office (prefixed)
  office_coworking: { color: '#7f7f7f', label: 'Coworking space' },
  // Club (prefixed)
  club_country_club: { color: '#2ca02c', label: 'Country club' },
  club_social: { color: '#2ca02c', label: 'Social club' },
  club_sport: { color: '#aec7e8', label: 'Sport club' },
  club_veterans: { color: '#8c564b', label: 'Veterans club' },
  club_youth: { color: '#bcbd22', label: 'Youth club' },
  club_charity: { color: '#17becf', label: 'Charity club' },
}

const FALLBACK: CategoryStyle = { color: '#7f7f7f', label: 'Other' }

export function styleForVenue(props: VenueProperties): CategoryStyle {
  return STYLES[props.category] ?? FALLBACK
}

export function allCategoryStyles(): Array<{ key: string } & CategoryStyle> {
  return Object.entries(STYLES).map(([key, s]) => ({ key, ...s }))
}
