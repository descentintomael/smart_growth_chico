import { Outlet, Link, useLocation } from 'react-router-dom'
import { PrintButton } from '@/components/ui/PrintButton'

export function Layout() {
  const location = useLocation()
  const isMapPage = location.pathname === '/' || location.pathname === ''

  return (
    <div className="flex h-screen w-screen flex-col">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center">
            <h1 className="text-lg font-semibold text-gray-900">Smart Growth Visualizer</h1>
            <span className="ml-2 text-sm text-gray-500">Chico, CA</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden items-center gap-4 md:flex">
            <Link
              to="/"
              className={`text-sm font-medium transition-colors ${
                isMapPage
                  ? 'text-primary-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Map
            </Link>
            <Link
              to="/methodology"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/methodology'
                  ? 'text-primary-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Methodology
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {isMapPage && <PrintButton className="hidden md:flex" />}

          {/* Mobile navigation */}
          <nav className="flex items-center gap-2 md:hidden">
            <Link
              to="/"
              className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                isMapPage
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Map
            </Link>
            <Link
              to="/methodology"
              className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                location.pathname === '/methodology'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              About
            </Link>
          </nav>
        </div>
      </header>

      {/* Page content */}
      <Outlet />
    </div>
  )
}
