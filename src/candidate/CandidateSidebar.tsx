import { allCategoryStyles } from './categoryStyle'
import { TopVenuesPanel } from './TopVenuesPanel'

interface SidebarProps {
  district: string
  collapsed: boolean
  onToggle: () => void
}

export function CandidateSidebar({ district, collapsed, onToggle }: SidebarProps) {
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
          Legend · D{district}
        </div>
      </aside>
    )
  }

  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto border-r border-gray-200 bg-white p-4 text-sm">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Candidate venue map</h2>
          <p className="mt-1 text-xs text-gray-500">District {district}, Chico CA</p>
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

      <TopVenuesPanel district={district} />

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Venue categories
        </h3>
        <ul className="mt-2 space-y-1">
          {allCategoryStyles().map(s => (
            <li key={s.key} className="flex items-center gap-2 text-xs">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span>{s.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Marker shape
        </h3>
        <ul className="mt-2 space-y-1.5 text-xs">
          <li className="flex items-center gap-2">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{ backgroundColor: '#374151' }}
            />
            <span>Filled = inside District {district}</span>
          </li>
          <li className="flex items-center gap-2">
            <span
              className="inline-block h-3 w-3 rounded-full border-2"
              style={{ borderColor: '#374151' }}
            />
            <span>Ring = adjacency zone (≤1 mi outside — walking catchment may still reach district residents)</span>
          </li>
        </ul>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Hosting status
        </h3>
        <ul className="mt-2 space-y-1 text-xs">
          <li className="flex items-center gap-2">
            <span className="inline-block rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide" style={{ backgroundColor: '#dcfce7', color: '#166534' }}>
              confirmed
            </span>
            <span className="text-gray-600">Evidence of rentability + access</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide" style={{ backgroundColor: '#fef9c3', color: '#854d0e' }}>
              likely
            </span>
            <span className="text-gray-600">Strong signals but a call needed</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide" style={{ backgroundColor: '#e5e7eb', color: '#374151' }}>
              needs verification
            </span>
            <span className="text-gray-600">No public info; phone call required</span>
          </li>
        </ul>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Catchments
        </h3>
        <p className="mt-2 text-xs text-gray-600">
          <strong>Click any venue</strong> to see its walking and biking catchment
          areas at 10 and 15 minutes, plus an estimated demographics breakdown for
          each band. Catchments are computed against the actual OSM road network —
          not radius circles.
        </p>
      </div>

      <div className="mt-auto rounded bg-amber-50 p-3 text-xs text-amber-900">
        <strong>Preview build.</strong> Venues sourced from OpenStreetMap, filtered
        for chains/gyms/fast-food, enriched by Google Places attributes and website
        assessments where available. Voter weighting currently uses estimated CVAP
        (citizen voting-age population) as a proxy; real precinct-level registered-
        voter counts can be substituted later without changing the UI.
      </div>
    </aside>
  )
}
