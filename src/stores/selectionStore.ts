import { create } from 'zustand'
import type { Feature, Geometry, GeoJsonProperties } from 'geojson'

interface SelectionState {
  selectedFeature: Feature<Geometry, GeoJsonProperties> | null
  hoveredFeature: Feature<Geometry, GeoJsonProperties> | null
  selectedLayerId: string | null
  setSelectedFeature: (feature: Feature<Geometry, GeoJsonProperties> | null, layerId?: string) => void
  setHoveredFeature: (feature: Feature<Geometry, GeoJsonProperties> | null) => void
  clearSelection: () => void
}

export const useSelectionStore = create<SelectionState>(set => ({
  selectedFeature: null,
  hoveredFeature: null,
  selectedLayerId: null,

  setSelectedFeature: (feature, layerId) =>
    set({
      selectedFeature: feature,
      selectedLayerId: layerId ?? null,
    }),

  setHoveredFeature: feature =>
    set({
      hoveredFeature: feature,
    }),

  clearSelection: () =>
    set({
      selectedFeature: null,
      selectedLayerId: null,
    }),
}))
