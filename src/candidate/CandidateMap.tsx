import { useEffect, useState } from 'react'
import {
  MapContainer as LeafletMapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Popup,
  ZoomControl,
} from 'react-leaflet'
import type { LatLngBoundsExpression, PathOptions } from 'leaflet'
import type { GeoJsonObject } from 'geojson'
import type {
  DistrictBoundaryCollection,
  VenueCollection,
  VenueFeature,
} from './types'
import { styleForVenue } from './categoryStyle'

const BOUNDARY_URL = `${import.meta.env.BASE_URL}data/candidate-district-6/district-boundary.geojson`
const VENUES_URL = `${import.meta.env.BASE_URL}data/candidate-district-6/venues.geojson`

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

function venueRadius(feature: VenueFeature): number {
  const excluded = feature.properties.hosting_status === 'excluded'
  return excluded ? 5 : 8
}

function venueOpacity(feature: VenueFeature): number {
  return feature.properties.hosting_status === 'excluded' ? 0.4 : 0.9
}

export function CandidateMap() {
  const [boundary, setBoundary] = useState<DistrictBoundaryCollection | null>(null)
  const [venues, setVenues] = useState<VenueCollection | null>(null)
  const [bounds, setBounds] = useState<LatLngBoundsExpression | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [b, v] = await Promise.all([
          fetch(BOUNDARY_URL).then(r => {
            if (!r.ok) throw new Error(`boundary ${r.status}`)
            return r.json() as Promise<DistrictBoundaryCollection>
          }),
          fetch(VENUES_URL).then(r => {
            if (!r.ok) throw new Error(`venues ${r.status}`)
            return r.json() as Promise<VenueCollection>
          }),
        ])
        if (cancelled) return
        setBoundary(b)
        setVenues(v)

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
  }, [])

  return (
    <div className="relative h-full w-full">
      <LeafletMapContainer
        center={CHICO_CENTER}
        zoom={DEFAULT_ZOOM}
        zoomControl={false}
        className="h-full w-full"
        bounds={bounds ?? undefined}
        boundsOptions={{ padding: [20, 20] }}
      >
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

        {venues?.features.map(f => {
          const style = styleForVenue(f.properties)
          const [lon, lat] = f.geometry.coordinates as [number, number]
          return (
            <CircleMarker
              key={f.properties.osm_id}
              center={[lat, lon]}
              radius={venueRadius(f)}
              pathOptions={{
                color: style.color,
                weight: 1,
                fillColor: style.color,
                fillOpacity: venueOpacity(f),
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold">{f.properties.name}</div>
                  <div className="text-xs text-gray-600">{style.label}</div>
                  {f.properties.address && (
                    <div className="mt-1 text-xs">{f.properties.address}</div>
                  )}
                  {f.properties.website && (
                    <a
                      href={f.properties.website}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="mt-1 block text-xs text-blue-600 hover:underline"
                    >
                      Website
                    </a>
                  )}
                  <div className="mt-2 inline-block rounded bg-gray-100 px-2 py-0.5 text-[10px] uppercase tracking-wide text-gray-700">
                    {f.properties.hosting_status.replace(/_/g, ' ')}
                  </div>
                  {f.properties.notes && (
                    <div className="mt-1 text-xs italic text-gray-500">
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
