import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { CandidateMap } from './CandidateMap'
import { CandidateSidebar } from './CandidateSidebar'

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

    document.title = 'Venue map (private preview)'

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

export function CandidateApp() {
  useNoIndexMeta()
  const { district } = useParams<{ district: string }>()
  const districtNum = district ?? '6'

  return (
    <div className="flex h-screen w-screen flex-col">
      <header className="flex h-12 shrink-0 items-center border-b border-gray-200 bg-gray-50 px-4">
        <span className="text-sm font-medium text-gray-700">
          Candidate venue map · District {districtNum}
        </span>
        <span className="ml-3 rounded bg-amber-100 px-2 py-0.5 text-[10px] uppercase tracking-wide text-amber-800">
          Private preview
        </span>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <CandidateSidebar district={districtNum} />
        <main className="relative flex-1">
          <CandidateMap district={districtNum} />
        </main>
      </div>
    </div>
  )
}
