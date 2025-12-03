import { create } from 'zustand'
import { LAYER_CONFIGS } from '@/data/layerConfig'

interface LayerState {
  visibleLayers: Set<string>
  layerOpacity: Record<string, number>
  toggleLayer: (layerId: string) => void
  setLayerOpacity: (layerId: string, opacity: number) => void
  showOnlyLayer: (layerId: string) => void
  resetLayers: () => void
}

// Initialize with default visible layers from config
const defaultVisibleLayers = new Set(
  LAYER_CONFIGS.filter((config) => config.defaultVisible).map((config) => config.id)
)

// Initialize all layers with full opacity
const defaultOpacity = Object.fromEntries(LAYER_CONFIGS.map((config) => [config.id, 1]))

export const useLayerStore = create<LayerState>((set) => ({
  visibleLayers: defaultVisibleLayers,
  layerOpacity: defaultOpacity,

  toggleLayer: (layerId) =>
    set((state) => {
      const newVisible = new Set(state.visibleLayers)
      if (newVisible.has(layerId)) {
        newVisible.delete(layerId)
      } else {
        newVisible.add(layerId)
      }
      return { visibleLayers: newVisible }
    }),

  setLayerOpacity: (layerId, opacity) =>
    set((state) => ({
      layerOpacity: { ...state.layerOpacity, [layerId]: opacity },
    })),

  showOnlyLayer: (layerId) =>
    set(() => ({
      visibleLayers: new Set([layerId]),
    })),

  resetLayers: () =>
    set(() => ({
      visibleLayers: defaultVisibleLayers,
      layerOpacity: defaultOpacity,
    })),
}))
