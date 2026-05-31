import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ForumMap } from './ForumMap'
import { ForumSidebar } from './ForumSidebar'
import { parseForumSlug } from './forumHelpers'

const ROBOTS_META_CONTENT = 'noindex, nofollow, noarchive, nosnippet'
const SIDEBAR_COLLAPSED_KEY = 'candidate-sidebar-collapsed'

function useNoIndexMeta() {
  useEffect(() => {
    const existing = document.querySelector<HTMLMetaElement>('meta[name="robots"]')
    const previous = existing?.getAttribute('content') ?? null
    const previousTitle = document.title

    const meta = existing ?? document.createElement('meta')
    meta.setAttribute('name', 'robots')
    meta.setAttribute('content', ROBOTS_META_CONTENT)
    if (!existing) document.head.appendChild(meta)

    document.title = 'Forum venue map (private preview)'

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

export function ForumApp() {
  useNoIndexMeta()
  const { slug } = useParams<{ slug: string }>()
  const districts = parseForumSlug(slug) ?? ['4', '6']

  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
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
      <header className="flex h-12 shrink-0 items-center border-b border-gray-200 bg-gray-50 px-4">
        <span className="text-sm font-medium text-gray-700">
          Forum venue map · Districts {districts.join(' + ')}
        </span>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <ForumSidebar
          districts={districts}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(v => !v)}
        />
        <main className="relative flex-1">
          <ForumMap districts={districts} />
        </main>
      </div>
    </div>
  )
}
