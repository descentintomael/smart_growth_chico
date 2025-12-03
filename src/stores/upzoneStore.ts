import { create } from 'zustand'
import type { UpzoneViewMode, UpzoneSummary } from '@/types'

interface UpzoneState {
  // View mode: show current or projected Smart Growth Index
  viewMode: UpzoneViewMode

  // Adoption percentage (0-100, continuous)
  adoptionPercent: number

  // Cached summary data for aggregate stats
  summary: UpzoneSummary | null

  // Loading state for summary
  summaryLoading: boolean

  // Actions
  setViewMode: (mode: UpzoneViewMode) => void
  setAdoptionPercent: (percent: number) => void
  setSummary: (summary: UpzoneSummary) => void
  setSummaryLoading: (loading: boolean) => void
}

export const useUpzoneStore = create<UpzoneState>((set) => ({
  viewMode: 'projected',
  adoptionPercent: 25,
  summary: null,
  summaryLoading: false,

  setViewMode: (mode) => set({ viewMode: mode }),

  setAdoptionPercent: (percent) =>
    set({ adoptionPercent: Math.max(0, Math.min(100, percent)) }),

  setSummary: (summary) => set({ summary, summaryLoading: false }),

  setSummaryLoading: (loading) => set({ summaryLoading: loading }),
}))
