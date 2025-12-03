import '@testing-library/jest-dom'

// Mock ResizeObserver for Leaflet
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock
