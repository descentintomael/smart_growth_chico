import { useEffect, useMemo, useState } from 'react'
import {
  MapContainer as LeafletMapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Marker,
  Popup,
  ZoomControl,
  useMap,
} from 'react-leaflet'
import L from 'leaflet'
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
import { ForumDemographicsPanel } from './ForumDemographicsPanel'
import { styleForVenue } from './categoryStyle'
import { useCandidateSelection } from './selectionStore'
import {
  colorForDistrict,
  mergeForumData,
  rescoreVenuesForForum,
  type VenueForumStats,
} from './forumHelpers'

const CHICO_CENTER: [number, number] = [39.7285, -121.8375]
const DEFAULT_ZOOM = 12

function FitToBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap()
  useEffect(() => {
    if (!bounds) return
    map.fitBounds(bounds, { padding: [0, 0] })
    map.setZoom(map.getZoom() + 1)
  }, [bounds, map])
  return null
}

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

function ZoomTracker({ onChange }: { onChange: (zoom: number) => void }) {
  const map = useMap()
  useEffect(() => {
    const handler = () => onChange(map.getZoom())
    handler()
    map.on('zoomend', handler)
    return () => { map.off('zoomend', handler) }
  }, [map, onChange])
  return null
}

function zoomScale(zoom: number): number {
  return Math.max(0, Math.min(1, (zoom - 12) / 3))
}

const CATCHMENT_LAYER_STYLE: Record<CatchmentProfile, PathOptions> = {
  walk_10:      { color: '#1e3a8a', weight: 1.5, fillColor: '#2563eb', fillOpacity: 0.55 },
  walk_15_only: { color: '#2563eb', weight: 1,   fillColor: '#60a5fa', fillOpacity: 0.45 },
  bike_10_only: { color: '#a16207', weight: 1,   fillColor: '#f59e0b', fillOpacity: 0.40 },
  bike_15_only: { color: '#b45309', weight: 1,   fillColor: '#fcd34d', fillOpacity: 0.30 },
  walk_15: { color: '#000', weight: 0, fillColor: '#000', fillOpacity: 0 },
  bike_10: { color: '#000', weight: 0, fillColor: '#000', fillOpacity: 0 },
  bike_15: { color: '#000', weight: 0, fillColor: '#000', fillOpacity: 0 },
}
const CATCHMENT_RENDER_ORDER: CatchmentProfile[] = [
  'bike_15_only', 'bike_10_only', 'walk_15_only', 'walk_10',
]

function venueRadius(feature: VenueFeature, zoom: number): number {
  const status = feature.properties.hosting_status
  const tier = feature.properties.priority_tier
  if (status === 'excluded') return 4
  if (tier === 'top') return 13
  if (tier === 'high') return 10
  const scale = zoomScale(zoom)
  if (tier === 'medium') return Math.max(2, Math.round(7 * (0.4 + 0.6 * scale)))
  if (tier === 'low')    return Math.max(1, Math.round(5 * (0.15 + 0.85 * scale)))
  return 7
}

function excludedIcon(isSelected: boolean): L.DivIcon {
  const color = isSelected ? '#111827' : '#9ca3af'
  return L.divIcon({
    className: 'venue-excluded-x',
    html: `<svg viewBox="0 0 16 16" width="16" height="16">
      <line x1="3.5" y1="3.5" x2="12.5" y2="12.5" stroke="${color}" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="12.5" y1="3.5" x2="3.5" y2="12.5" stroke="${color}" stroke-width="2.5" stroke-linecap="round"/>
    </svg>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  })
}

async function loadDistrict(district: string) {
  const base = `${import.meta.env.BASE_URL}data/candidate-district-${district}`
  const [boundary, venues, catchments, demo] = await Promise.all([
    fetch(`${base}/district-boundary.geojson`).then(r => r.json() as Promise<DistrictBoundaryCollection>),
    fetch(`${base}/venues.geojson`).then(r => r.json() as Promise<VenueCollection>),
    fetch(`${base}/catchments.geojson`).then(r => r.ok ? r.json() as Promise<CatchmentCollection> : null).catch(() => null),
    fetch(`${base}/catchment-demographics.json`).then(r => r.ok ? r.json() as Promise<CatchmentDemographics> : null).catch(() => null),
  ])
  return { district, boundary, venues, catchments, demo }
}

export function ForumMap({ districts }: { districts: string[] }) {
  const [perDistrict, setPerDistrict] = useState<
    Array<Awaited<ReturnType<typeof loadDistrict>>> | null
  >(null)
  const [bounds, setBounds] = useState<LatLngBoundsExpression | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [zoom, setZoom] = useState(DEFAULT_ZOOM)
  const selectedVenueId = useCandidateSelection(s => s.selectedVenueId)
  const setSelectedVenueId = useCandidateSelection(s => s.setSelectedVenueId)

  useEffect(() => {
    let cancelled = false
    Promise.all(districts.map(loadDistrict))
      .then(results => {
        if (cancelled) return
        setPerDistrict(results)
        // Compute combined bbox from all boundaries
        const coords: [number, number][] = []
        for (const r of results) {
          for (const f of r.boundary.features) {
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
        }
        if (coords.length) {
          const lats = coords.map(c => c[0])
          const lons = coords.map(c => c[1])
          setBounds([
            [Math.min(...lats), Math.min(...lons)],
            [Math.max(...lats), Math.max(...lons)],
          ])
        }
      })
      .catch(err => {
        if (!cancelled) setLoadError(String(err))
      })
    return () => { cancelled = true }
  }, [districts])

  const merged = useMemo<Map<string, VenueForumStats> | null>(() => {
    if (!perDistrict) return null
    const input: Record<string, { venues: VenueCollection; demo: CatchmentDemographics }> = {}
    for (const r of perDistrict) {
      if (r.demo) input[r.district] = { venues: r.venues, demo: r.demo }
    }
    return mergeForumData(input)
  }, [perDistrict])

  const venues = useMemo<VenueFeature[]>(() => {
    if (!merged) return []
    return rescoreVenuesForForum(merged, districts)
  }, [merged, districts])

  // Combined catchments for the currently selected venue, pulled from
  // whichever district's catchment file happens to contain it.
  const selectedCatchments = useMemo<CatchmentCollection | null>(() => {
    if (!perDistrict || !selectedVenueId) return null
    for (const r of perDistrict) {
      if (!r.catchments) continue
      const found = r.catchments.features.find(f => f.properties.venue_id === selectedVenueId)
      if (found) return r.catchments
    }
    return null
  }, [perDistrict, selectedVenueId])

  const selectedVenue = useMemo(
    () => venues.find(v => v.properties.osm_id === selectedVenueId),
    [venues, selectedVenueId]
  )

  return (
    <div className="relative h-full w-full">
      {selectedVenue && merged && (
        <div className="absolute left-4 top-4 bottom-4 z-[1000] flex w-80 max-w-[calc(100vw-2rem)] flex-col">
          <div className="shrink-0 rounded-md bg-white/95 px-3 py-2 text-xs shadow-lg ring-1 ring-gray-200 backdrop-blur">
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
                <span>Walk · 0–10 min</span>
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
          <ForumDemographicsPanel
            stats={merged.get(selectedVenueId!)}
            districts={districts}
          />
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
        <ZoomTracker onChange={setZoom} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
          maxZoom={20}
        />

        {/* District boundaries, one per selected district, each in a different color. */}
        {perDistrict?.map(r => (
          <GeoJSON
            key={`boundary-${r.district}`}
            data={r.boundary as unknown as GeoJsonObject}
            style={() => ({
              color: colorForDistrict(r.district, districts),
              weight: 3,
              fillColor: colorForDistrict(r.district, districts),
              fillOpacity: 0.05,
              dashArray: '6 4',
            })}
            interactive={false}
          />
        ))}

        {/* Catchment shells for the selected venue. */}
        {selectedCatchments && selectedVenueId &&
          CATCHMENT_RENDER_ORDER.map(profile => {
            const feature = selectedCatchments.features.find(
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

        {venues.map(f => {
          const style = styleForVenue(f.properties)
          const [lon, lat] = f.geometry.coordinates as [number, number]
          const isSelected = selectedVenueId === f.properties.osm_id

          if (f.properties.hosting_status === 'excluded') {
            return (
              <Marker
                key={f.properties.osm_id}
                position={[lat, lon]}
                icon={excludedIcon(isSelected)}
                eventHandlers={{
                  click: () => setSelectedVenueId(f.properties.osm_id),
                }}
              >
                <Popup maxWidth={340}>
                  <div className="text-sm">
                    <div className="font-semibold">{f.properties.name}</div>
                    <div className="text-xs text-gray-600">Excluded · {style.label}</div>
                    {f.properties.notes && (
                      <div className="mt-1 text-xs text-gray-700">{f.properties.notes}</div>
                    )}
                  </div>
                </Popup>
              </Marker>
            )
          }

          return (
            <CircleMarker
              key={f.properties.osm_id}
              center={[lat, lon]}
              radius={isSelected ? venueRadius(f, zoom) + 3 : venueRadius(f, zoom)}
              pathOptions={{
                color: isSelected ? '#111827' : style.color,
                weight: isSelected ? 3 : (f.properties.priority_tier === 'top' ? 3 : 1.5),
                fillColor: style.color,
                fillOpacity: 0.85,
                opacity: 0.95,
              }}
              eventHandlers={{
                click: () => setSelectedVenueId(f.properties.osm_id),
              }}
            >
              <Popup maxWidth={300}>
                <div className="text-sm">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-semibold">{f.properties.name}</span>
                    {f.properties.google_rating != null && (
                      <span className="shrink-0 text-xs text-gray-600">
                        {f.properties.google_rating.toFixed(1)}★
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-600">{style.label}</div>
                  {f.properties.priority_score != null && (
                    <div className="mt-2 rounded border border-gray-200 bg-gray-50 px-2 py-1">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="uppercase tracking-wide text-gray-500">Union priority</span>
                        <span className="font-semibold tabular-nums">
                          #{f.properties.priority_rank} · {f.properties.priority_score.toFixed(2)}
                        </span>
                      </div>
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
          Failed to load forum data: {loadError}
        </div>
      )}
    </div>
  )
}
