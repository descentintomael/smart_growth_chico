import { useEffect, useState } from 'react'
import type { VenueCollection, VenueFeature } from './types'
import { useCandidateSelection } from './selectionStore'
import { styleForVenue } from './categoryStyle'

const TIER_COLOR: Record<NonNullable<VenueFeature['properties']['priority_tier']>, string> = {
  top: '#16a34a',
  high: '#65a30d',
  medium: '#ca8a04',
  low: '#94a3b8',
}

export function TopVenuesPanel({ district }: { district: string }) {
  const [venues, setVenues] = useState<VenueFeature[] | null>(null)
  const selectedVenueId = useCandidateSelection(s => s.selectedVenueId)
  const setSelectedVenueId = useCandidateSelection(s => s.setSelectedVenueId)

  useEffect(() => {
    let cancelled = false
    const url = `${import.meta.env.BASE_URL}data/candidate-district-${district}/venues.geojson`
    fetch(url)
      .then(r => (r.ok ? (r.json() as Promise<VenueCollection>) : null))
      .then(data => {
        if (cancelled || !data) return
        const ranked = data.features
          .filter(f => f.properties.priority_rank != null)
          .sort((a, b) => (a.properties.priority_rank! - b.properties.priority_rank!))
          .slice(0, 10)
        setVenues(ranked)
      })
      .catch(() => {})
    return () => { cancelled = true }
  }, [district])

  if (!venues || venues.length === 0) return null

  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
        Top 10 forum venues
      </h3>
      <p className="mt-1 text-[10px] leading-snug text-gray-500">
        Composite score: 40% in-district reach, 25% hosting confidence, 25% forum fit, 10% legitimacy.
      </p>
      <ol className="mt-2 space-y-1">
        {venues.map(v => {
          const p = v.properties
          const style = styleForVenue(p)
          const tierColor = p.priority_tier ? TIER_COLOR[p.priority_tier] : '#94a3b8'
          const isSelected = p.osm_id === selectedVenueId
          return (
            <li key={p.osm_id}>
              <button
                onClick={() => setSelectedVenueId(p.osm_id)}
                className={`group flex w-full items-center gap-2 rounded px-1.5 py-1 text-left text-[11px] transition-colors ${
                  isSelected ? 'bg-gray-900 text-white' : 'hover:bg-gray-100'
                }`}
              >
                <span
                  className={`inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                    isSelected ? 'bg-white text-gray-900' : 'text-white'
                  }`}
                  style={isSelected ? undefined : { backgroundColor: '#111827' }}
                >
                  {p.priority_rank}
                </span>
                <span className="flex-1 truncate">
                  <span className="block truncate font-medium">{p.name}</span>
                  <span className={`block truncate text-[10px] ${isSelected ? 'text-gray-300' : 'text-gray-500'}`}>
                    {style.label}
                    {p.in_district === false && ' · adjacency'}
                  </span>
                </span>
                <span
                  className="shrink-0 text-[10px] tabular-nums font-semibold"
                  style={{ color: isSelected ? 'white' : tierColor }}
                >
                  {p.priority_score?.toFixed(2) ?? '–'}
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
