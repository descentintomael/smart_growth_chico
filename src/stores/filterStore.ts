import { create } from 'zustand'

export interface LayerFilter {
  property: string
  min?: number
  max?: number
}

interface FilterState {
  filters: Record<string, LayerFilter>
  setFilter: (layerId: string, property: string, min?: number, max?: number) => void
  clearLayerFilter: (layerId: string) => void
  clearAllFilters: () => void
}

export const useFilterStore = create<FilterState>(set => ({
  filters: {},

  setFilter: (layerId, property, min, max) =>
    set(state => ({
      filters: {
        ...state.filters,
        [layerId]: { property, min, max },
      },
    })),

  clearLayerFilter: layerId =>
    set(state => {
      const { [layerId]: _, ...rest } = state.filters
      return { filters: rest }
    }),

  clearAllFilters: () => set({ filters: {} }),
}))
