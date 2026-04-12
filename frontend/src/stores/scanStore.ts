import { create } from 'zustand'
import { api, WS_URL } from '../api/client'
import { useAuthStore } from './authStore'
import type { Scan, AgentLog, Finding, PendingAction, Target } from '../types'

/** Solicitud de aprobación llegada via WebSocket (type: command_request) */
export interface CommandRequest {
  action_id: string
  tool_name: string
  command: string
  human_explanation: string
  why_needed: string
  risk_explanation: string
  risk_level: string
  scan_id: string | null
  timestamp: string
}

/** Salida de un comando llegada via WebSocket (type: command_output) */
export interface CommandOutput {
  tool_name: string
  scan_id: string | null
  lines: string[]
  timestamp: string
}

/** Entrada en el panel de terminal */
export interface TerminalEntry {
  id: string
  kind: 'log' | 'command_request' | 'command_output'
  timestamp: string
  tool_name?: string
  message?: string
  log_level?: string
  lines?: string[]
  risk_level?: string
}

interface ScanStore {
  targets: Target[]
  scans: Scan[]
  findings: Finding[]
  pendingActions: PendingAction[]
  logs: AgentLog[]
  terminalEntries: TerminalEntry[]
  wsConnected: boolean
  pendingCommandRequest: CommandRequest | null

  fetchTargets: () => Promise<void>
  fetchScans: () => Promise<void>
  fetchFindings: (targetId?: string) => Promise<void>
  fetchPendingActions: () => Promise<void>
  startScan: (targetId: string, scanType?: string) => Promise<void>
  reviewAction: (actionId: string, decision: 'approved' | 'rejected', notes?: string) => Promise<void>
  connectWebSocket: () => void
  addLog: (log: AgentLog) => void
  clearPendingCommandRequest: () => void
  clearTerminal: () => void
}

export const useScanStore = create<ScanStore>((set, get) => ({
  targets: [],
  scans: [],
  findings: [],
  pendingActions: [],
  logs: [],
  terminalEntries: [],
  wsConnected: false,
  pendingCommandRequest: null,

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

        // Ping de keep-alive: ignorar
        if (data.type === 'ping') return

        // Solicitud de aprobación de herramienta
        if (data.type === 'command_request') {
          const req = data as CommandRequest
          set({ pendingCommandRequest: req })
          // Agregar al terminal como entrada de tipo request
          set((state) => ({
            terminalEntries: [
              ...state.terminalEntries,
              {
                id: `req-${req.action_id}`,
                kind: 'command_request',
                timestamp: req.timestamp,
                tool_name: req.tool_name,
                message: `⏳ Esperando aprobación: ${req.tool_name}`,
                risk_level: req.risk_level,
              } as TerminalEntry,
            ].slice(-2000),
          }))
          get().fetchPendingActions()
          return
        }

        // Output de un comando ya ejecutado
        if (data.type === 'command_output') {
          const out = data as CommandOutput
          if (out.lines && out.lines.length > 0) {
            set((state) => ({
              terminalEntries: [
                ...state.terminalEntries,
                {
                  id: `out-${out.tool_name}-${Date.now()}`,
                  kind: 'command_output',
                  timestamp: out.timestamp,
                  tool_name: out.tool_name,
                  lines: out.lines,
                } as TerminalEntry,
              ].slice(-2000),
            }))
          }
          return
        }

        // Log genérico — agregar a logs y al terminal
        get().addLog(data)
        get().fetchScans()
        get().fetchPendingActions()
      } catch {}
    }
  },

  addLog: (log: AgentLog) => {
    set((state) => ({
      logs: [log, ...state.logs].slice(0, 5000),
      terminalEntries: [
        ...state.terminalEntries,
        {
          id: log.id || `log-${Date.now()}`,
          kind: 'log',
          timestamp: log.created_at || new Date().toISOString(),
          message: log.message,
          log_level: log.log_level,
          tool_name: log.component,
        } as TerminalEntry,
      ].slice(-2000),
    }))
  },

  clearPendingCommandRequest: () => set({ pendingCommandRequest: null }),

  clearTerminal: () => set({ terminalEntries: [] }),
}))
