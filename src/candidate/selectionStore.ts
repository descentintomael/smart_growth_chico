import { create } from 'zustand'

interface CandidateSelectionState {
  selectedVenueId: string | null
  setSelectedVenueId: (id: string | null) => void
}

/** Selection state shared between the map markers and the sidebar's top-venues list. */
export const useCandidateSelection = create<CandidateSelectionState>(set => ({
  selectedVenueId: null,
  setSelectedVenueId: id => set({ selectedVenueId: id }),
}))
