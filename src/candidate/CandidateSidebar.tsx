import { allCategoryStyles } from './categoryStyle'

export function CandidateSidebar({ district }: { district: string }) {
  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto border-r border-gray-200 bg-white p-4 text-sm">
      <div>
        <h2 className="text-base font-semibold text-gray-900">Candidate venue map</h2>
        <p className="mt-1 text-xs text-gray-500">District {district}, Chico CA</p>
      </div>

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
            <span>Filled = inside District 6</span>
          </li>
          <li className="flex items-center gap-2">
            <span
              className="inline-block h-3 w-3 rounded-full border-2"
              style={{ borderColor: '#374151' }}
            />
            <span>Ring = adjacency zone (≤1 mi from D6 — walking catchment may reach D6 residents)</span>
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
          <strong>Click any venue</strong> to see its walking (blue) and biking (green)
          catchment areas at 10 and 15 minutes. Catchments are computed against the
          actual OSM road network — not just radius circles.
        </p>
      </div>

      <div className="mt-auto rounded bg-amber-50 p-3 text-xs text-amber-900">
        <strong>Preview build.</strong> Venues sourced from OpenStreetMap, filtered for
        chains/gyms/fast-food, enriched by Google Places attributes and website
        assessments where available. Demographic overlays (registered voters, ACS
        block groups) are next.
      </div>
    </aside>
  )
}
