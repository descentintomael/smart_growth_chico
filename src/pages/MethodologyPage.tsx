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
    <main className="flex flex-1 flex-col overflow-hidden bg-gray-50">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <nav className="-mb-px flex space-x-1 overflow-x-auto py-2" aria-label="Methodology sections">
            {METHODOLOGY_SECTIONS.map((methodSection) => (
              <Link
                key={methodSection.id}
                to={`/methodology/${methodSection.id}`}
                className={`whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  activeSection === methodSection.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                }`}
              >
                {methodSection.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
          {/* Back to map link */}
          <Link
            to="/"
            className="mb-6 inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
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
            <>
              {/* Methodology content */}
              <article className="rounded-lg bg-white p-6 shadow-sm sm:p-8 lg:p-10">
                <div className="prose prose-gray max-w-none prose-headings:text-gray-900 prose-h1:text-3xl prose-h2:text-2xl prose-h2:border-b prose-h2:border-gray-200 prose-h2:pb-2 prose-h3:text-xl prose-a:text-primary-600 prose-table:text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                </div>
              </article>

              {/* Footer */}
              <div className="mt-8 text-center text-sm text-gray-500">
                <Link to="/" className="text-primary-600 hover:text-primary-700">
                  Return to Map Visualization
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  )
}
