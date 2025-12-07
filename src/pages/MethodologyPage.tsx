import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Link, useParams } from 'react-router-dom'

const METHODOLOGY_SECTIONS = [
  { id: 'smart-growth-index', label: 'Smart Growth Index' },
  { id: 'under-utilization', label: 'Under-Utilization' },
  { id: 'commercial-viability', label: 'Commercial Viability' },
  { id: 'parking-retrofit', label: 'Parking Retrofit' },
  { id: 'vacant-infill', label: 'Vacant Infill' },
  { id: 'commercial-retrofit', label: 'Commercial Retrofit' },
] as const

type SectionId = (typeof METHODOLOGY_SECTIONS)[number]['id']

export function MethodologyPage() {
  const { section } = useParams<{ section?: string }>()
  const activeSection: SectionId = METHODOLOGY_SECTIONS.some((s) => s.id === section)
    ? (section as SectionId)
    : 'smart-growth-index'

  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)

    fetch(`${import.meta.env.BASE_URL}methodology/${activeSection}.md`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load methodology')
        return res.text()
      })
      .then((text) => {
        setContent(text)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [activeSection])

  return (
    <main className="flex flex-1 overflow-hidden bg-gray-50">
      {/* Sidebar Navigation */}
      <aside className="flex w-64 flex-shrink-0 flex-col border-r border-gray-200 bg-white">
        {/* Back to map link */}
        <div className="border-b border-gray-200 px-4 py-4">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to Map
          </Link>
        </div>

        {/* Section Navigation */}
        <nav className="flex-1 overflow-y-auto p-4" aria-label="Methodology sections">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
            Methodology
          </h2>
          <ul className="space-y-1">
            {METHODOLOGY_SECTIONS.map((methodSection) => (
              <li key={methodSection.id}>
                <Link
                  to={`/methodology/${methodSection.id}`}
                  className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    activeSection === methodSection.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {methodSection.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-8 py-8">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-500">Loading methodology...</div>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center gap-4 py-12">
              <div className="text-red-600">Error: {error}</div>
              <Link to="/" className="text-primary-600 hover:text-primary-700">
                Return to Map
              </Link>
            </div>
          ) : (
            <article className="rounded-lg bg-white p-6 shadow-sm sm:p-8 lg:p-10">
              <div className="prose prose-gray max-w-none prose-headings:text-gray-900 prose-h1:text-3xl prose-h2:text-2xl prose-h2:border-b prose-h2:border-gray-200 prose-h2:pb-2 prose-h3:text-xl prose-a:text-primary-600 prose-table:text-sm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              </div>
            </article>
          )}
        </div>
      </div>
    </main>
  )
}
