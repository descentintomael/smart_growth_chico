import { useEffect, useState } from 'react'
import {
  MapContainer as LeafletMapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Popup,
  Tooltip,
  ZoomControl,
  useMap,
} from 'react-leaflet'
import type { LatLngBoundsExpression, PathOptions } from 'leaflet'
import type { GeoJsonObject } from 'geojson'
import type {
  CatchmentCollection,
  CatchmentDemographics,
  CatchmentProfile,
  DistrictBoundaryCollection,
  VenueCollection,
  VenueFeature,
} from './types'
import { CatchmentDemographicsPanel } from './CatchmentDemographicsPanel'
import { styleForVenue } from './categoryStyle'
import { useCandidateSelection } from './selectionStore'

// Shell-based rendering: each band is a geometrically distinct ring (or innermost
// disk) with no overlap, so a single solid fill per band reads clearly. The four
// shell profiles tile the full bike_15 catchment with no gaps and no overlaps.
const CATCHMENT_LAYER_STYLE: Record<CatchmentProfile, PathOptions> = {
  walk_10:      { color: '#1e3a8a', weight: 1.5, fillColor: '#2563eb', fillOpacity: 0.55 },
  walk_15_only: { color: '#2563eb', weight: 1,   fillColor: '#60a5fa', fillOpacity: 0.45 },
  bike_10_only: { color: '#a16207', weight: 1,   fillColor: '#f59e0b', fillOpacity: 0.40 },
  bike_15_only: { color: '#b45309', weight: 1,   fillColor: '#fcd34d', fillOpacity: 0.30 },
  // Full polygons (not normally rendered — kept for demographics aggregation only)
  walk_15: { color: '#000', weight: 0, fillColor: '#000', fillOpacity: 0 },
  bike_10: { color: '#000', weight: 0, fillColor: '#000', fillOpacity: 0 },
  bike_15: { color: '#000', weight: 0, fillColor: '#000', fillOpacity: 0 },
}

// Render order: largest (outermost) shell first, smallest (innermost) last.
// Because shells don't overlap, this z-order only matters for the highlighted borders.
const CATCHMENT_RENDER_ORDER: CatchmentProfile[] = [
  'bike_15_only',
  'bike_10_only',
  'walk_15_only',
  'walk_10',
]

/** Re-fits the map view when the boundary bounds become available.
 *  react-leaflet only honors center/zoom/bounds at mount, so we update
 *  imperatively via the map handle. */
function FitToBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap()
  useEffect(() => {
    if (!bounds) return
    // Tight fit (no padding). Then nudge zoom up by one step so the boundary
    // dominates the viewport — fitBounds alone tends to over-leave whitespace.
    map.fitBounds(bounds, { padding: [0, 0] })
    map.setZoom(map.getZoom() + 1)
  }, [bounds, map])
  return null
}

/** Leaflet doesn't auto-detect container size changes (sidebar collapse,
 *  window resize, etc.). Calls invalidateSize() whenever the container
 *  resizes so tiles fill the new dimensions. */
function InvalidateOnResize() {
  const map = useMap()
  useEffect(() => {
    const container = map.getContainer()
    const observer = new ResizeObserver(() => map.invalidateSize())
    observer.observe(container)
    return () => observer.disconnect()
  }, [map])
  return null
}

function dataUrls(district: string) {
  const base = `${import.meta.env.BASE_URL}data/candidate-district-${district}`
  return {
    boundary: `${base}/district-boundary.geojson`,
    venues: `${base}/venues.geojson`,
    catchments: `${base}/catchments.geojson`,
    catchmentDemographics: `${base}/catchment-demographics.json`,
  }
}

// Center fallback — overridden by fitBounds when the boundary loads.
const CHICO_CENTER: [number, number] = [39.7285, -121.8375]
const DEFAULT_ZOOM = 12

const BOUNDARY_STYLE: PathOptions = {
  color: '#1f2937',
  weight: 2.5,
  fillColor: '#1f2937',
  fillOpacity: 0.05,
  dashArray: '6 4',
}

/** Marker size scales with priority tier so the strongest forum hosts are
 *  visually dominant. Excluded venues are deliberately tiny. */
function venueRadius(feature: VenueFeature): number {
  const status = feature.properties.hosting_status
  const tier = feature.properties.priority_tier
  if (status === 'excluded') return 4
  if (tier === 'top') return 13
  if (tier === 'high') return 10
  if (tier === 'medium') return 7
  if (tier === 'low') return 5
  // Venue hasn't been scored — fall back to a confidence-based size.
  if (status === 'confirmed') return 10
  if (status === 'likely') return 8
  return 7
}

function venueFillOpacity(feature: VenueFeature): number {
  if (feature.properties.hosting_status === 'excluded') {
    return feature.properties.in_district ? 0.25 : 0
  }
  // In-district = solid fill. Adjacency = ring only (no fill) so they read as secondary.
  if (!feature.properties.in_district) return 0
  return 0.85
}

function venueBorderWeight(feature: VenueFeature): number {
  if (feature.properties.hosting_status === 'excluded') return 2
  if (feature.properties.priority_tier === 'top') return 3
  return feature.properties.in_district ? 1.5 : 2.5
}

function venueBorderOpacity(feature: VenueFeature): number {
  if (feature.properties.hosting_status === 'excluded') return 0.85
  return 0.95
}

function venueBorderColor(feature: VenueFeature, fallback: string, isSelected: boolean): string {
  if (feature.properties.hosting_status === 'excluded') return '#dc2626'
  if (isSelected) return '#111827'
  return fallback
}

function priorityBreakdownBar(label: string, value: number, color: string) {
  return (
    <div key={label} className="grid grid-cols-[5rem_minmax(0,1fr)_2.5rem] items-center gap-1.5 text-[10px]">
      <span className="text-gray-600">{label}</span>
      <div className="h-1.5 rounded-sm bg-gray-100">
        <div
          className="h-full rounded-sm"
          style={{ width: `${Math.min(value * 100, 100)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-right tabular-nums text-gray-700">{value.toFixed(2)}</span>
    </div>
  )
}

function statusBadge(status: VenueFeature['properties']['hosting_status']): {
  label: string
  bg: string
  fg: string
} {
  switch (status) {
    case 'confirmed':
      return { label: 'confirmed', bg: '#dcfce7', fg: '#166534' }
    case 'likely':
      return { label: 'likely', bg: '#fef9c3', fg: '#854d0e' }
    case 'excluded':
      return { label: 'excluded', bg: '#fee2e2', fg: '#991b1b' }
    case 'needs_verification':
    default:
      return { label: 'needs verification', bg: '#e5e7eb', fg: '#374151' }
  }
}

export function CandidateMap({ district }: { district: string }) {
  const [boundary, setBoundary] = useState<DistrictBoundaryCollection | null>(null)
  const [venues, setVenues] = useState<VenueCollection | null>(null)
  const [catchments, setCatchments] = useState<CatchmentCollection | null>(null)
  const [catchmentDemo, setCatchmentDemo] = useState<CatchmentDemographics | null>(null)
  const selectedVenueId = useCandidateSelection(s => s.selectedVenueId)
  const setSelectedVenueId = useCandidateSelection(s => s.setSelectedVenueId)
  const [bounds, setBounds] = useState<LatLngBoundsExpression | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const urls = dataUrls(district)
    async function load() {
      try {
        const [b, v, c, d] = await Promise.all([
          fetch(urls.boundary).then(r => {
            if (!r.ok) throw new Error(`boundary ${r.status}`)
            return r.json() as Promise<DistrictBoundaryCollection>
          }),
          fetch(urls.venues).then(r => {
            if (!r.ok) throw new Error(`venues ${r.status}`)
            return r.json() as Promise<VenueCollection>
          }),
          // Catchments are optional — older builds may not have them.
          fetch(urls.catchments).then(r => {
            if (!r.ok) return null
            return r.json() as Promise<CatchmentCollection>
          }).catch(() => null),
          // Catchment demographics are also optional.
          fetch(urls.catchmentDemographics).then(r => {
            if (!r.ok) return null
            return r.json() as Promise<CatchmentDemographics>
          }).catch(() => null),
        ])
        if (cancelled) return
        setBoundary(b)
        setVenues(v)
        setCatchments(c)
        setCatchmentDemo(d)

        // Compute simple bbox for fitBounds
        const coords: [number, number][] = []
        for (const f of b.features) {
          const geom = f.geometry
          const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates
          for (const poly of polys) {
            for (const ring of poly) {
              for (const [lon, lat] of ring as [number, number][]) {
                coords.push([lat, lon])
              }
            }
          }
        }
        if (coords.length) {
          const lats = coords.map(c => c[0])
          const lons = coords.map(c => c[1])
          setBounds([
            [Math.min(...lats), Math.min(...lons)],
            [Math.max(...lats), Math.max(...lons)],
          ])
        }
      } catch (err) {
        if (!cancelled) setLoadError(String(err))
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [district])

  const selectedVenue = selectedVenueId
    ? venues?.features.find(f => f.properties.osm_id === selectedVenueId)
    : null

  return (
    <div className="relative h-full w-full">
      {selectedVenue && (
        <div className="absolute left-4 top-4 z-[1000] w-80 max-w-[calc(100vw-2rem)]">
          <div className="rounded-md bg-white/95 px-3 py-2 text-xs shadow-lg ring-1 ring-gray-200 backdrop-blur">
          <div className="flex items-center justify-between gap-2">
            <span className="font-semibold text-gray-900">{selectedVenue.properties.name}</span>
            <button
              onClick={() => setSelectedVenueId(null)}
              className="text-gray-400 hover:text-gray-700"
              aria-label="Clear selection"
            >
              ✕
            </button>
          </div>
          <div className="mt-1 text-[10px] uppercase tracking-wide text-gray-500">Catchment bands</div>
          <ul className="mt-1 space-y-0.5">
            <li className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: '#2563eb', opacity: 0.55 }} />
              <span>Walk · 0–10 min (~½ mi)</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: '#60a5fa', opacity: 0.45 }} />
              <span>Walk · 10–15 min</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: '#f59e0b', opacity: 0.4 }} />
              <span>Bike · &lt;10 min beyond walk</span>
            </li>
            <li className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: '#fcd34d', opacity: 0.3 }} />
              <span>Bike · 10–15 min</span>
            </li>
          </ul>
          </div>
          <CatchmentDemographicsPanel data={catchmentDemo} venueId={selectedVenueId} district={district} />
        </div>
      )}
      <LeafletMapContainer
        center={CHICO_CENTER}
        zoom={DEFAULT_ZOOM}
        zoomControl={false}
        className="h-full w-full"
      >
        <FitToBounds bounds={bounds} />
        <InvalidateOnResize />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
          maxZoom={20}
        />

        {boundary && (
          <GeoJSON
            key="district-boundary"
            data={boundary as unknown as GeoJsonObject}
            style={() => BOUNDARY_STYLE}
            interactive={false}
          />
        )}

        {/* Catchment overlays for the currently-selected venue. Only the shell features
            are rendered — they tile the full bike_15 area with no overlaps, so each
            band has a single clean color with no alpha-stacking artifacts. */}
        {catchments && selectedVenueId &&
          CATCHMENT_RENDER_ORDER.map(profile => {
            const feature = catchments.features.find(
              f =>
                f.properties.venue_id === selectedVenueId &&
                f.properties.profile === profile &&
                f.properties.feature_type === 'shell'
            )
            if (!feature) return null
            return (
              <GeoJSON
                key={`catch-${selectedVenueId}-${profile}`}
                data={feature as unknown as GeoJsonObject}
                style={() => CATCHMENT_LAYER_STYLE[profile]}
                interactive={false}
              />
            )
          })}

        {venues?.features.map(f => {
          const style = styleForVenue(f.properties)
          const [lon, lat] = f.geometry.coordinates as [number, number]
          const badge = statusBadge(f.properties.hosting_status)
          const isSelected = selectedVenueId === f.properties.osm_id
          return (
            <CircleMarker
              key={f.properties.osm_id}
              center={[lat, lon]}
              radius={isSelected ? venueRadius(f) + 3 : venueRadius(f)}
              pathOptions={{
                color: venueBorderColor(f, style.color, isSelected),
                weight: isSelected ? 3 : venueBorderWeight(f),
                fillColor: style.color,
                fillOpacity: venueFillOpacity(f),
                opacity: venueBorderOpacity(f),
              }}
              eventHandlers={{
                click: () => setSelectedVenueId(f.properties.osm_id),
              }}
            >
              {f.properties.hosting_status === 'excluded' && (
                <Tooltip
                  permanent
                  direction="top"
                  offset={[0, -venueRadius(f) - 2]}
                  className="venue-excluded-tooltip"
                >
                  ✕
                </Tooltip>
              )}
              <Popup maxWidth={340}>
                <div className="text-sm">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-semibold">{f.properties.name}</span>
                    {f.properties.google_rating != null && (
                      <span className="shrink-0 text-xs text-gray-600">
                        {f.properties.google_rating.toFixed(1)}★
                        {f.properties.google_user_ratings_count != null && (
                          <span className="text-gray-400"> · {f.properties.google_user_ratings_count.toLocaleString()}</span>
                        )}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-600">
                    {style.label}
                    {!f.properties.in_district && (
                      <span className="ml-1 text-gray-400">· adjacency</span>
                    )}
                  </div>
                  {(f.properties.google_formatted_address || f.properties.address) && (
                    <div className="mt-1 text-xs text-gray-700">
                      {f.properties.google_formatted_address ?? f.properties.address}
                    </div>
                  )}
                  {(f.properties.website || f.properties.phone) && (
                    <div className="mt-1 flex flex-wrap gap-3 text-xs">
                      {f.properties.website && (
                        <a
                          href={f.properties.website}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="text-blue-600 hover:underline"
                        >
                          Website
                        </a>
                      )}
                      {f.properties.phone && (
                        <a
                          href={`tel:${f.properties.phone.replace(/\s/g, '')}`}
                          className="text-blue-600 hover:underline"
                        >
                          {f.properties.phone}
                        </a>
                      )}
                    </div>
                  )}
                  {f.properties.google_editorial_summary && (
                    <div className="mt-2 rounded bg-gray-50 px-2 py-1.5 text-xs italic text-gray-700">
                      “{f.properties.google_editorial_summary}”
                    </div>
                  )}
                  {f.properties.priority_score != null && (
                    <div className="mt-2 rounded border border-gray-200 bg-gray-50 px-2 py-1.5">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="uppercase tracking-wide text-gray-500">Forum priority</span>
                        <span className="font-semibold tabular-nums text-gray-900">
                          #{f.properties.priority_rank} · {f.properties.priority_score.toFixed(2)}
                          <span className="ml-1 font-normal text-gray-500">({f.properties.priority_tier})</span>
                        </span>
                      </div>
                      {f.properties.priority_components && (
                        <div className="mt-1 space-y-0.5">
                          {priorityBreakdownBar('Audience', f.properties.priority_components.audience, '#3b82f6')}
                          {priorityBreakdownBar('Confidence', f.properties.priority_components.confidence, '#10b981')}
                          {priorityBreakdownBar('Forum fit', f.properties.priority_components.fit, '#f59e0b')}
                          {priorityBreakdownBar('Legitimacy', f.properties.priority_components.legitimacy, '#8b5cf6')}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    <span
                      className="inline-block rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                      style={{ backgroundColor: badge.bg, color: badge.fg }}
                    >
                      {badge.label}
                    </span>
                    {f.properties.google_business_status &&
                      f.properties.google_business_status !== 'OPERATIONAL' && (
                        <span className="inline-block rounded bg-red-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-700">
                          {f.properties.google_business_status.replace('_', ' ').toLowerCase()}
                        </span>
                      )}
                    {f.properties.assessment_confidence && (
                      <span className="text-[10px] uppercase tracking-wide text-gray-400">
                        conf: {f.properties.assessment_confidence}
                      </span>
                    )}
                  </div>
                  {f.properties.notes && (
                    <div className="mt-2 whitespace-pre-line text-xs text-gray-700">
                      {f.properties.notes}
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          )
        })}

        <ZoomControl position="bottomright" />
      </LeafletMapContainer>

      {loadError && (
        <div className="absolute left-1/2 top-4 z-[1000] -translate-x-1/2 rounded bg-red-50 px-3 py-2 text-sm text-red-700 shadow">
          Failed to load data: {loadError}
        </div>
      )}
    </div>
  )
}
