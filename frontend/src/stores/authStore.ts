/**
 * Auth Store — Zustand + localStorage persistence
 * Maneja: login, logout, refresh, estado del usuario
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface UserMe {
  id: string
  username: string
  email: string
  role: string
  is_active: boolean
  last_login: string | null
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: UserMe | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshTokens: () => Promise<void>
  fetchMe: () => Promise<void>
  initialize: () => Promise<void>
  clearError: () => void
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${API_BASE}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Login failed')
          }

          const data = await response.json()
          set({
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            isAuthenticated: true,
            error: null,
          })

          // Cargar info del usuario
          await get().fetchMe()
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed'
          set({ error: message, isLoading: false })
          throw err
        } finally {
          set({ isLoading: false })
        }
      },

      logout: async () => {
        set({ isLoading: true })
        try {
          const token = get().accessToken
          if (token) {
            await fetch(`${API_BASE}/auth/logout/`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
            })
          }
        } finally {
          set({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          })
        }
      },

      refreshTokens: async () => {
        const refreshToken = get().refreshToken
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

        try {
          const response = await fetch(`${API_BASE}/auth/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })

          if (!response.ok) {
            // Refresh failed — logout
            set({
              accessToken: null,
              refreshToken: null,
              isAuthenticated: false,
            })
            throw new Error('Refresh token invalid or expired')
          }

          const data = await response.json()
          set({ accessToken: data.access_token })
        } catch (err) {
          set({
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
          })
          throw err
        }
      },

      fetchMe: async () => {
        const token = get().accessToken
        if (!token) {
          throw new Error('No access token')
        }

        try {
          const response = await fetch(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          })

          if (!response.ok) {
            throw new Error('Failed to fetch user info')
          }

          const user = await response.json()
          set({ user })
        } catch (err) {
          console.error('Failed to fetch user:', err)
          throw err
        }
      },

      initialize: async () => {
        const token = get().accessToken
        if (!token) {
          set({ isAuthenticated: false })
          return
        }

        try {
          await get().fetchMe()
          set({ isAuthenticated: true })
        } catch (err) {
          // Si fetchMe falla, intenta refresh
          try {
            await get().refreshTokens()
            await get().fetchMe()
            set({ isAuthenticated: true })
          } catch {
            set({
              accessToken: null,
              refreshToken: null,
              isAuthenticated: false,
            })
          }
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'sysmho-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)
