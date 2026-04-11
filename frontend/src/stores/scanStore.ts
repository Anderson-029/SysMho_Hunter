import { create } from 'zustand'
import { api, WS_URL } from '../api/client'
import { useAuthStore } from './authStore'
import type { Scan, AgentLog, Finding, PendingAction, Target } from '../types'

interface ScanStore {
  targets: Target[]
  scans: Scan[]
  findings: Finding[]
  pendingActions: PendingAction[]
  logs: AgentLog[]
  wsConnected: boolean

  fetchTargets: () => Promise<void>
  fetchScans: () => Promise<void>
  fetchFindings: (targetId?: string) => Promise<void>
  fetchPendingActions: () => Promise<void>
  startScan: (targetId: string, scanType?: string) => Promise<void>
  reviewAction: (actionId: string, decision: 'approved' | 'rejected', notes?: string) => Promise<void>
  connectWebSocket: () => void
  addLog: (log: AgentLog) => void
}

export const useScanStore = create<ScanStore>((set, get) => ({
  targets: [],
  scans: [],
  findings: [],
  pendingActions: [],
  logs: [],
  wsConnected: false,

  fetchTargets: async () => {
    try {
      const res = await api.get('/targets/')
      set({ targets: res ?? [] })
    } catch { set({ targets: [] }) }
  },

  fetchScans: async () => {
    try {
      const res = await api.get('/scans/')
      set({ scans: res ?? [] })
    } catch { set({ scans: [] }) }
  },

  fetchFindings: async (targetId?: string) => {
    try {
      const url = targetId ? `/findings/?target_id=${targetId}` : '/findings/'
      const res = await api.get(url)
      set({ findings: res ?? [] })
    } catch { set({ findings: [] }) }
  },

  fetchPendingActions: async () => {
    try {
      const res = await api.get('/actions/')
      set({ pendingActions: res ?? [] })
    } catch { set({ pendingActions: [] }) }
  },

  startScan: async (targetId: string, scanType = 'full') => {
    await api.post('/scans/', { target_id: targetId, scan_type: scanType })
    await get().fetchScans()
  },

  reviewAction: async (actionId: string, decision: 'approved' | 'rejected', notes?: string) => {
    await api.post(`/actions/${actionId}/review`, { decision, review_notes: notes })
    await get().fetchPendingActions()
  },

  connectWebSocket: () => {
    const authStore = useAuthStore.getState()
    const token = authStore.accessToken

    // Construir URL con token si existe
    let wsUrl = WS_URL
    if (token) {
      wsUrl = `${WS_URL}?token=${encodeURIComponent(token)}`
    }

    const ws = new WebSocket(wsUrl)
    ws.onopen = () => set({ wsConnected: true })
    ws.onclose = () => {
      set({ wsConnected: false })
      setTimeout(() => get().connectWebSocket(), 3000)
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'ping') return
        get().addLog(data)
        // Refrescar scans si hay actualizaciones
        get().fetchScans()
        get().fetchPendingActions()
      } catch {}
    }
  },

  addLog: (log: AgentLog) => {
    set((state) => ({
      logs: [log, ...state.logs].slice(0, 5000)
    }))
  },
}))
