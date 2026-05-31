import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { MapPage } from './pages/MapPage'
import { MethodologyPage } from './pages/MethodologyPage'
import { CandidateApp } from './candidate/CandidateApp'
import './styles/globals.css'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Root element not found')

createRoot(rootElement).render(
  <StrictMode>
    <HashRouter>
      <Routes>
        {/* Candidate map: standalone, outside shared Layout. Sets its own noindex meta. */}
        {/* Slug is a whole segment (React Router v6 dynamic params can't be partial),
            so URL is /candidate/district-6, /candidate/district-4, etc. CandidateApp
            parses the slug to extract the district number. */}
        <Route path="candidate/:slug" element={<CandidateApp />} />

        <Route element={<Layout />}>
          <Route index element={<MapPage />} />
          <Route path="methodology/:section?" element={<MethodologyPage />} />
        </Route>
      </Routes>
    </HashRouter>
  </StrictMode>
)
