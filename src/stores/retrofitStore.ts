import { create } from 'zustand'
import type {
  ParkingRetrofitSummary,
  VacantInfillSummary,
  CommercialRetrofitSummary,
} from '@/types'

interface RetrofitState {
  // Parking Retrofit (no adoption slider - shows full potential)
  parkingSummary: ParkingRetrofitSummary | null
  parkingLoading: boolean

  // Vacant Infill (with adoption slider)
  vacantAdoption: number // 0-100
  vacantSummary: VacantInfillSummary | null
  vacantLoading: boolean

  // Commercial Retrofit (with adoption slider)
  commercialAdoption: number // 0-100
  commercialSummary: CommercialRetrofitSummary | null
  commercialLoading: boolean

  // Actions
  setParkingSummary: (summary: ParkingRetrofitSummary) => void
  setParkingLoading: (loading: boolean) => void

  setVacantAdoption: (percent: number) => void
  setVacantSummary: (summary: VacantInfillSummary) => void
  setVacantLoading: (loading: boolean) => void

  setCommercialAdoption: (percent: number) => void
  setCommercialSummary: (summary: CommercialRetrofitSummary) => void
  setCommercialLoading: (loading: boolean) => void
}

export const useRetrofitStore = create<RetrofitState>((set) => ({
  // Parking Retrofit
  parkingSummary: null,
  parkingLoading: false,

  // Vacant Infill
  vacantAdoption: 100, // Default to full buildout
  vacantSummary: null,
  vacantLoading: false,

  // Commercial Retrofit
  commercialAdoption: 100, // Default to full buildout
  commercialSummary: null,
  commercialLoading: false,

  // Actions
  setParkingSummary: (summary) => set({ parkingSummary: summary, parkingLoading: false }),
  setParkingLoading: (loading) => set({ parkingLoading: loading }),

  setVacantAdoption: (percent) =>
    set({ vacantAdoption: Math.max(0, Math.min(100, percent)) }),
  setVacantSummary: (summary) => set({ vacantSummary: summary, vacantLoading: false }),
  setVacantLoading: (loading) => set({ vacantLoading: loading }),

  setCommercialAdoption: (percent) =>
    set({ commercialAdoption: Math.max(0, Math.min(100, percent)) }),
  setCommercialSummary: (summary) =>
    set({ commercialSummary: summary, commercialLoading: false }),
  setCommercialLoading: (loading) => set({ commercialLoading: loading }),
}))
