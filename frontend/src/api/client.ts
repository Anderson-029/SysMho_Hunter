/**
 * API Client — axios + interceptores para JWT/API Key
 */

import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-api-key-change-in-production'

export const WS_URL = `${API_BASE.replace('http://', 'ws://').replace('https://', 'wss://')}/ws/live`

const axiosInstance = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
})

// Request: inyectar Bearer token o API Key
axiosInstance.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  } else {
    config.headers['X-API-Key'] = API_KEY
  }
  return config
})

// Response: manejar 401 → refresh → reintentar
axiosInstance.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }
    original._retry = true
    try {
      await useAuthStore.getState().refreshTokens()
      return axiosInstance(original)
    } catch {
      useAuthStore.getState().logout()
      return Promise.reject(error)
    }
  }
)

export const api = {
  get: (endpoint: string) =>
    axiosInstance.get(endpoint).then((r) => r.data),
  post: (endpoint: string, body: unknown) =>
    axiosInstance.post(endpoint, body).then((r) => r.data),
  put: (endpoint: string, body: unknown) =>
    axiosInstance.put(endpoint, body).then((r) => r.data),
  delete: (endpoint: string) =>
    axiosInstance.delete(endpoint).then((r) => r.data),
}

export default axiosInstance
