/**
 * API Client — Incluye API Key en todos los requests
 */

const API_BASE = 'http://localhost:8000/api/v1'

// API Key — obtener desde import.meta.env (configurable en .env del frontend)
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-api-key-change-in-production'

interface FetchOptions extends RequestInit {
  body?: any
}

/**
 * Fetch wrapper que incluye header X-API-Key en todos los requests
 */
export async function apiCall(
  endpoint: string,
  options: FetchOptions = {}
): Promise<any> {
  const url = `${API_BASE}${endpoint}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    ...(options.headers as Record<string, string>),
  }

  const config: RequestInit = {
    ...options,
    headers,
  }

  if (options.body && typeof options.body !== 'string') {
    config.body = JSON.stringify(options.body)
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `API Error: ${response.status}`)
  }

  return response.json().catch(() => null)
}

// Métodos HTTP helper
export const api = {
  get: (endpoint: string) =>
    apiCall(endpoint, { method: 'GET' }),

  post: (endpoint: string, body: any) =>
    apiCall(endpoint, { method: 'POST', body }),

  put: (endpoint: string, body: any) =>
    apiCall(endpoint, { method: 'PUT', body }),

  delete: (endpoint: string) =>
    apiCall(endpoint, { method: 'DELETE' }),
}
