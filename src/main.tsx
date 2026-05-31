import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { MapPage } from './pages/MapPage'
import { MethodologyPage } from './pages/MethodologyPage'
import { CandidateApp } from './candidate/CandidateApp'
import { ForumApp } from './candidate/ForumApp'
import './styles/globals.css'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Root element not found')

createRoot(rootElement).render(
  <StrictMode>
    <HashRouter>
      <Routes>
        {/* Forum map: multi-district view. URL is /candidate/forum/4-6 (hyphen-separated
            district numbers). Must appear before the single-district route. */}
        <Route path="candidate/forum/:slug" element={<ForumApp />} />

        {/* Single-district candidate map. URL is /candidate/district-6, etc. */}
        <Route path="candidate/:slug" element={<CandidateApp />} />

        <Route element={<Layout />}>
          <Route index element={<MapPage />} />
          <Route path="methodology/:section?" element={<MethodologyPage />} />
        </Route>
      </Routes>
    </HashRouter>
  </StrictMode>
)
