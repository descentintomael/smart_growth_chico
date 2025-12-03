import { create } from 'zustand'
import type { CommercialViabilitySummary } from '@/types'

interface CommercialViabilityState {
  // Adoption percentage (0-100, continuous)
  adoptionPercent: number

  // Cached summary data for aggregate stats
  summary: CommercialViabilitySummary | null

  // Loading state for summary
  summaryLoading: boolean

  // Actions
  setAdoptionPercent: (percent: number) => void
  setSummary: (summary: CommercialViabilitySummary) => void
  setSummaryLoading: (loading: boolean) => void
}

export const useCommercialViabilityStore = create<CommercialViabilityState>((set) => ({
  adoptionPercent: 100, // Default to full buildout
  summary: null,
  summaryLoading: false,

  setAdoptionPercent: (percent) =>
    set({ adoptionPercent: Math.max(0, Math.min(100, percent)) }),

  setSummary: (summary) => set({ summary, summaryLoading: false }),

  setSummaryLoading: (loading) => set({ summaryLoading: loading }),
}))
