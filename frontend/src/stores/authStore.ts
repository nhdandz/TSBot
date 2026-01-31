// Authentication store

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { adminService } from '@/services/adminService'
import type { LoginRequest } from '@/types'

interface User {
  username: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (credentials: LoginRequest) => Promise<boolean>
  logout: () => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null })
        try {
          const response = await adminService.login(credentials)

          if (response.access_token) {
            set({
              user: { username: credentials.username, role: 'admin' },
              token: response.access_token,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            })
            return true
          } else {
            set({
              error: 'Đăng nhập thất bại',
              isLoading: false,
            })
            return false
          }
        } catch (error: any) {
          set({
            error: error.detail || 'Lỗi kết nối đến server',
            isLoading: false,
          })
          return false
        }
      },

      logout: () => {
        localStorage.removeItem('auth_token')
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
