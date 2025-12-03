import { useState } from 'react'
import { MapContainer } from './components/map/MapContainer'
import { Legend } from './components/ui/Legend'
import { LayerControl } from './components/panels/LayerControl'
import { InfoPanel } from './components/panels/InfoPanel'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen w-screen flex-col">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4">
        <div className="flex items-center">
          <h1 className="text-lg font-semibold text-gray-900">Smart Growth Visualizer</h1>
          <span className="ml-2 text-sm text-gray-500">Chico, CA</span>
        </div>

        {/* Sidebar toggle for mobile */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 md:hidden"
          aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {sidebarOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </header>

      {/* Main content */}
      <main className="relative flex flex-1 overflow-hidden">
        {/* Sidebar - desktop always visible, mobile toggleable */}
        <aside
          className={`
            absolute inset-y-0 left-0 z-20 flex w-80 flex-col border-r border-gray-200 bg-white
            transition-transform duration-300 ease-in-out
            md:relative md:translate-x-0
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
        >
          <LayerControl />
          <div className="border-t border-gray-200">
            <InfoPanel />
          </div>
        </aside>

        {/* Map container */}
        <div className="relative flex-1">
          <MapContainer />
          <Legend />
        </div>

        {/* Mobile overlay when sidebar is open */}
        {sidebarOpen && (
          <div
            className="absolute inset-0 z-10 bg-black/20 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </main>
    </div>
  )
}
