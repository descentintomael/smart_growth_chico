import { create } from 'zustand'
import type { UnderUtilizationMetric, UnderUtilizationSummary } from '@/types'

interface UnderUtilizationState {
  // Selected metric to display
  selectedMetric: UnderUtilizationMetric

  // Cached summary data for aggregate stats
  summary: UnderUtilizationSummary | null

  // Loading state for summary
  summaryLoading: boolean

  // Actions
  setMetric: (metric: UnderUtilizationMetric) => void
  setSummary: (summary: UnderUtilizationSummary) => void
  setSummaryLoading: (loading: boolean) => void
}

export const useUnderUtilizationStore = create<UnderUtilizationState>((set) => ({
  selectedMetric: 'composite',
  summary: null,
  summaryLoading: false,

  setMetric: (metric) => set({ selectedMetric: metric }),

  setSummary: (summary) => set({ summary, summaryLoading: false }),

  setSummaryLoading: (loading) => set({ summaryLoading: loading }),
}))
