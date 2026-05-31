import { useEffect, useState } from 'react'
import type { CatchmentDemographics, VenueCollection, VenueFeature } from './types'
import { useCandidateSelection } from './selectionStore'
import { colorForDistrict, mergeForumData, rescoreVenuesForForum } from './forumHelpers'

interface SidebarProps {
  districts: string[]
  collapsed: boolean
  onToggle: () => void
}

export function ForumSidebar({ districts, collapsed, onToggle }: SidebarProps) {
  const [topVenues, setTopVenues] = useState<VenueFeature[] | null>(null)
  const selectedVenueId = useCandidateSelection(s => s.selectedVenueId)
  const setSelectedVenueId = useCandidateSelection(s => s.setSelectedVenueId)

  useEffect(() => {
    let cancelled = false
    Promise.all(
      districts.map(async d => {
        const base = `${import.meta.env.BASE_URL}data/candidate-district-${d}`
        const [venues, demo] = await Promise.all([
          fetch(`${base}/venues.geojson`).then(r => r.json() as Promise<VenueCollection>),
          fetch(`${base}/catchment-demographics.json`).then(r => r.json() as Promise<CatchmentDemographics>),
        ])
        return { district: d, venues, demo }
      })
    )
      .then(results => {
        if (cancelled) return
        const input = Object.fromEntries(
          results.map(r => [r.district, { venues: r.venues, demo: r.demo }])
        )
        const merged = mergeForumData(input)
        const rescored = rescoreVenuesForForum(merged, districts)
        setTopVenues(rescored.slice(0, 10))
      })
      .catch(() => {})
    return () => { cancelled = true }
  }, [districts])

  if (collapsed) {
    return (
      <aside className="flex w-8 shrink-0 flex-col items-center border-r border-gray-200 bg-white py-3">
        <button
          onClick={onToggle}
          className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-900"
          aria-label="Expand sidebar"
          title="Expand legend"
        >
          <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
            <path d="M6 4l8 6-8 6V4z" />
          </svg>
        </button>
        <div className="mt-3 [writing-mode:vertical-rl] [text-orientation:mixed] text-[10px] uppercase tracking-wider text-gray-400">
          Forum · D{districts.join('+D')}
        </div>
      </aside>
    )
  }

  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto border-r border-gray-200 bg-white p-4 text-sm">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Forum venue map</h2>
          <p className="mt-1 text-xs text-gray-500">Districts {districts.join(' + ')}</p>
        </div>
        <button
          onClick={onToggle}
          className="-mr-1 -mt-1 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
          aria-label="Collapse sidebar"
          title="Collapse legend"
        >
          <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
            <path d="M14 4l-8 6 8 6V4z" />
          </svg>
        </button>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          District boundaries
        </h3>
        <ul className="mt-2 space-y-1 text-xs">
          {districts.map(d => (
            <li key={d} className="flex items-center gap-2">
              <span
                className="inline-block h-3 w-6 rounded-sm"
                style={{ backgroundColor: colorForDistrict(d, districts), opacity: 0.6 }}
              />
              <span>District {d}</span>
            </li>
          ))}
        </ul>
      </div>

      {topVenues && topVenues.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Top 10 forum venues
          </h3>
          <p className="mt-1 text-[10px] leading-snug text-gray-500">
            Ranked by <strong>balanced</strong> reach (geometric mean of
            per-district CVAPs). Venues that don't reach ALL selected districts
            score low even if their total audience is large.
          </p>
          <ol className="mt-2 space-y-1">
            {topVenues.map(v => {
              const p = v.properties
              const isSelected = p.osm_id === selectedVenueId
              return (
                <li key={p.osm_id}>
                  <button
                    onClick={() => setSelectedVenueId(p.osm_id)}
                    className={`group flex w-full items-center gap-2 rounded px-1.5 py-1 text-left text-[11px] ${
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
                        {(p.priority_components?.in_district_walk_15_cvap ?? 0).toLocaleString()} CVAP in union
                      </span>
                    </span>
                    <span className="flex shrink-0 flex-col items-end">
                      <span className={`text-[10px] tabular-nums font-semibold ${
                        isSelected ? 'text-white' : 'text-gray-700'
                      }`}>
                        {p.priority_score?.toFixed(2) ?? '–'}
                      </span>
                      {p.forum_districts_with_reach != null && p.forum_districts_total != null && (
                        <span
                          className={`text-[9px] tabular-nums ${
                            p.forum_districts_with_reach === p.forum_districts_total
                              ? (isSelected ? 'text-green-300' : 'text-green-700')
                              : (isSelected ? 'text-amber-200' : 'text-amber-700')
                          }`}
                        >
                          {p.forum_districts_with_reach}/{p.forum_districts_total}
                        </span>
                      )}
                    </span>
                  </button>
                </li>
              )
            })}
          </ol>
        </div>
      )}

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          About this view
        </h3>
        <p className="mt-2 text-xs text-gray-600">
          Each venue's score combines audience reach (the sum of in-district CVAP across the
          selected districts), hosting confidence, forum fit, and legitimacy. Click any venue
          to see how its catchment splits across the selected districts.
        </p>
      </div>
    </aside>
  )
}
