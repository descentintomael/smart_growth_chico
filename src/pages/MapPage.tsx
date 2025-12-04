import { useState } from 'react'
import { MapContainer } from '@/components/map/MapContainer'
import { Legend } from '@/components/ui/Legend'
import { UpzoneLegend } from '@/components/ui/UpzoneLegend'
import { CommercialViabilityLegend } from '@/components/ui/CommercialViabilityLegend'
import { RetrofitLegend } from '@/components/ui/RetrofitLegend'
import { LayerControl } from '@/components/panels/LayerControl'
import { FilterPanel } from '@/components/panels/FilterPanel'
import { UnderUtilizationControlPanel } from '@/components/panels/UnderUtilizationControlPanel'
import { UpzoneControlPanel } from '@/components/panels/UpzoneControlPanel'
import { CommercialViabilityControlPanel } from '@/components/panels/CommercialViabilityControlPanel'
import { RetrofitControlPanel } from '@/components/panels/RetrofitControlPanel'
import { InfoPanel } from '@/components/panels/InfoPanel'

export function MapPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <main className="relative flex flex-1 overflow-hidden">
      {/* Sidebar toggle button (mobile only) */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute right-4 top-4 z-30 rounded-md bg-white p-2 text-gray-500 shadow-md hover:bg-gray-100 hover:text-gray-700 md:hidden"
        aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          {sidebarOpen ? (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          ) : (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          )}
        </svg>
      </button>

      {/* Sidebar - desktop always visible, mobile toggleable */}
      <aside
        className={`
          absolute inset-y-0 left-0 z-20 flex w-80 flex-col border-r border-gray-200 bg-white overflow-y-auto
          transition-transform duration-300 ease-in-out
          md:relative md:translate-x-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <LayerControl />
        <UnderUtilizationControlPanel />
        <UpzoneControlPanel />
        <CommercialViabilityControlPanel />
        <RetrofitControlPanel />
        <FilterPanel />
        <InfoPanel />
      </aside>

      {/* Map container */}
      <div className="relative flex-1">
        <MapContainer />
        <Legend />
        <UpzoneLegend />
        <CommercialViabilityLegend />
        <RetrofitLegend />
      </div>

      {/* Mobile overlay when sidebar is open */}
      {sidebarOpen && (
        <div
          className="absolute inset-0 z-10 bg-black/20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </main>
  )
}
