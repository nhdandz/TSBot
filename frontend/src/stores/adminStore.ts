// Admin data store

import { create } from 'zustand'
import type { Truong, Nganh, DiemChuanView, DashboardStats } from '@/types'

interface AdminState {
  // Data
  truong: Truong[]
  nganh: Nganh[]
  diemChuan: DiemChuanView[]
  stats: DashboardStats | null

  // UI State
  isLoading: boolean
  error: string | null

  // Actions
  setTruong: (truong: Truong[]) => void
  addTruong: (school: Truong) => void
  updateTruong: (schoolId: string, school: Truong) => void
  removeTruong: (schoolId: string) => void

  setNganh: (nganh: Nganh[]) => void
  addNganh: (major: Nganh) => void
  updateNganh: (majorCode: string, major: Nganh) => void
  removeNganh: (majorCode: string) => void

  setDiemChuan: (diemChuan: DiemChuanView[]) => void
  setStats: (stats: DashboardStats) => void

  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAdminStore = create<AdminState>((set) => ({
  truong: [],
  nganh: [],
  diemChuan: [],
  stats: null,
  isLoading: false,
  error: null,

  setTruong: (truong) => set({ truong }),
  addTruong: (school) =>
    set((state) => ({
      truong: [...state.truong, school],
    })),
  updateTruong: (schoolId, school) =>
    set((state) => ({
      truong: state.truong.map((s) => (s.school_id === schoolId ? school : s)),
    })),
  removeTruong: (schoolId) =>
    set((state) => ({
      truong: state.truong.filter((s) => s.school_id !== schoolId),
    })),

  setNganh: (nganh) => set({ nganh }),
  addNganh: (major) =>
    set((state) => ({
      nganh: [...state.nganh, major],
    })),
  updateNganh: (majorCode, major) =>
    set((state) => ({
      nganh: state.nganh.map((n) => (n.major_code === majorCode ? major : n)),
    })),
  removeNganh: (majorCode) =>
    set((state) => ({
      nganh: state.nganh.filter((n) => n.major_code !== majorCode),
    })),

  setDiemChuan: (diemChuan) => set({ diemChuan }),
  setStats: (stats) => set({ stats }),

  setIsLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}))
