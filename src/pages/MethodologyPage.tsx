import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Link } from 'react-router-dom'

export function MethodologyPage() {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}methodology.md`)
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
  }, [])

  if (loading) {
    return (
      <main className="flex flex-1 items-center justify-center bg-gray-50">
        <div className="text-gray-500">Loading methodology...</div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center bg-gray-50 gap-4">
        <div className="text-red-600">Error: {error}</div>
        <Link to="/" className="text-primary-600 hover:text-primary-700">
          Return to Map
        </Link>
      </main>
    )
  }

  return (
    <main className="flex-1 overflow-y-auto bg-gray-50">
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
      </div>
    </main>
  )
}
