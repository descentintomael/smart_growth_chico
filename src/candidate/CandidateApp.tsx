import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { CandidateMap } from './CandidateMap'
import { CandidateSidebar } from './CandidateSidebar'
import { DistrictMultiSelect } from './DistrictMultiSelect'

const SIDEBAR_COLLAPSED_KEY = 'candidate-sidebar-collapsed'

const ROBOTS_META_CONTENT = 'noindex, nofollow, noarchive, nosnippet'

function useNoIndexMeta() {
  useEffect(() => {
    const existing = document.querySelector<HTMLMetaElement>('meta[name="robots"]')
    const previous = existing?.getAttribute('content') ?? null
    const previousTitle = document.title

    const meta = existing ?? document.createElement('meta')
    meta.setAttribute('name', 'robots')
    meta.setAttribute('content', ROBOTS_META_CONTENT)
    if (!existing) document.head.appendChild(meta)

    document.title = 'Venue map'

    return () => {
      if (previous === null) {
        meta.remove()
      } else {
        meta.setAttribute('content', previous)
      }
      document.title = previousTitle
    }
  }, [])
}

// Parse a URL slug like "district-6" into the bare district number "6".
function parseDistrictFromSlug(slug: string | undefined): string {
  if (!slug) return '6'
  const match = slug.match(/^district-(\d+)$/)
  return match?.[1] ?? '6'
}

export function CandidateApp() {
  useNoIndexMeta()
  const { slug } = useParams<{ slug: string }>()
  const districtNum = parseDistrictFromSlug(slug)

  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
      // Default collapsed on first visit; honor stored choice on later visits.
      if (stored === null) return true
      return stored === '1'
    } catch {
      return true
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, sidebarCollapsed ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [sidebarCollapsed])

  return (
    <div className="flex h-screen w-screen flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-gray-200 bg-gray-50 px-4">
        <span className="text-sm font-medium text-gray-700">Venue map</span>
        <DistrictMultiSelect selectedDistricts={[districtNum]} />
      </header>
      <div className="flex flex-1 overflow-hidden">
        <CandidateSidebar
          district={districtNum}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(v => !v)}
        />
        <main className="relative flex-1">
          <CandidateMap district={districtNum} />
        </main>
      </div>
    </div>
  )
}
