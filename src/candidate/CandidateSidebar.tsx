import { allCategoryStyles } from './categoryStyle'

export function CandidateSidebar() {
  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto border-r border-gray-200 bg-white p-4 text-sm">
      <div>
        <h2 className="text-base font-semibold text-gray-900">Candidate venue map</h2>
        <p className="mt-1 text-xs text-gray-500">District 6, Chico CA</p>
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
          Status legend
        </h3>
        <ul className="mt-2 space-y-1 text-xs">
          <li className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-400" />
            <span>Solid = candidate worth pursuing</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-400 opacity-40" />
            <span>Faded = auto-excluded</span>
          </li>
        </ul>
      </div>

      <div className="mt-auto rounded bg-amber-50 p-3 text-xs text-amber-900">
        <strong>Preview build.</strong> Venues are an initial OSM dump filtered to
        District 6, with national chains auto-excluded. Capacity, accessibility,
        and political-event policy still need confirmation per venue. Walk/bike
        catchments and demographics are not yet wired in.
      </div>
    </aside>
  )
}
