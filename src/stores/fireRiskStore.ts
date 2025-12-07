import { create } from 'zustand'
import type { FireRiskSummary } from '@/types'

interface FireRiskState {
  // Cached summary data for aggregate stats
  summary: FireRiskSummary | null

  // Loading state for summary
  summaryLoading: boolean

  // Actions
  setSummary: (summary: FireRiskSummary) => void
  setSummaryLoading: (loading: boolean) => void
}

export const useFireRiskStore = create<FireRiskState>((set) => ({
  summary: null,
  summaryLoading: false,

  setSummary: (summary) => set({ summary, summaryLoading: false }),

  setSummaryLoading: (loading) => set({ summaryLoading: loading }),
}))
