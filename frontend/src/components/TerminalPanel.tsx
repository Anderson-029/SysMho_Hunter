/**
 * TerminalPanel — terminal visual en tiempo real que muestra qué está
 * haciendo SysMho Hunter: comandos ejecutados, outputs, aprobaciones, errores.
 *
 * Reutiliza @tanstack/react-virtual para listas grandes (igual que LiveLogs).
 */
import { useEffect, useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Terminal, Trash2, ChevronDown } from 'lucide-react'
import { useScanStore } from '../stores/scanStore'
import type { TerminalEntry } from '../stores/scanStore'

/* ── Colores por tipo de entrada ─────────────────────────────────── */
const LOG_LEVEL_COLOR: Record<string, string> = {
  debug: '#6b7280',
  info: '#e5e7eb',
  warning: '#ffd700',
  error: '#ff3366',
  critical: '#ff3366',
  success: '#00ff88',
}

const RISK_COLOR: Record<string, string> = {
  critical: '#ff3366',
  high: '#f97316',
  medium: '#ffd700',
  low: '#00bfff',
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return '--:--:--'
  }
}

/* ── Render de una línea del terminal ─────────────────────────────── */
function TerminalLine({ entry }: { entry: TerminalEntry }) {
  const ts = (
    <span
      className="text-xs font-mono mr-2"
      style={{ color: '#374151', flexShrink: 0 }}
    >
      [{formatTime(entry.timestamp)}]
    </span>
  )

  if (entry.kind === 'command_request') {
    const riskColor = RISK_COLOR[entry.risk_level ?? 'low'] ?? '#ffd700'
    return (
      <div
        className="flex items-start gap-1 py-0.5 px-2 rounded"
        style={{ backgroundColor: riskColor + '10' }}
      >
        {ts}
        <span
          className="text-xs font-mono"
          style={{ color: riskColor }}
        >
          ⏳
        </span>
        <span className="text-xs" style={{ color: riskColor }}>
          Esperando aprobación:{' '}
          <span className="font-bold">
            {entry.tool_name?.toUpperCase()}
          </span>{' '}
          <span style={{ color: '#4b5563' }}>
            (riesgo {entry.risk_level?.toUpperCase()})
          </span>
        </span>
      </div>
    )
  }

  if (entry.kind === 'command_output') {
    return (
      <div className="py-0.5">
        {/* Encabezado del output */}
        <div className="flex items-start gap-1 px-2">
          {ts}
          <span className="text-xs font-mono" style={{ color: '#00ff88' }}>
            ▶
          </span>
          <span
            className="text-xs font-bold font-mono"
            style={{ color: '#00bfff' }}
          >
            {entry.tool_name?.toUpperCase()}
          </span>
          <span className="text-xs font-mono" style={{ color: '#4b5563' }}>
            — output:
          </span>
        </div>
        {/* Líneas del output */}
        {entry.lines?.map((line, i) => (
          <div
            key={i}
            className="flex items-start gap-1 px-2 pl-8"
          >
            <span
              className="text-xs font-mono"
              style={{ color: '#9ca3af', wordBreak: 'break-all' }}
            >
              {line}
            </span>
          </div>
        ))}
      </div>
    )
  }

  /* log genérico */
  const levelColor =
    LOG_LEVEL_COLOR[entry.log_level ?? 'info'] ?? '#e5e7eb'
  const prefix =
    entry.log_level === 'warning'
      ? '⚠'
      : entry.log_level === 'error' || entry.log_level === 'critical'
        ? '✗'
        : entry.log_level === 'success'
          ? '✓'
          : '›'

  return (
    <div className="flex items-start gap-1 py-0.5 px-2">
      {ts}
      <span
        className="text-xs font-mono"
        style={{ color: levelColor, flexShrink: 0 }}
      >
        {prefix}
      </span>
      {entry.tool_name && (
        <span
          className="text-xs font-mono"
          style={{ color: '#4b5563', flexShrink: 0 }}
        >
          [{entry.tool_name}]
        </span>
      )}
      <span
        className="text-xs font-mono"
        style={{ color: levelColor, wordBreak: 'break-all' }}
      >
        {entry.message}
      </span>
    </div>
  )
}

/* ── Panel principal ─────────────────────────────────────────────── */
export function TerminalPanel() {
  const { terminalEntries, clearTerminal } = useScanStore()
  const parentRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const autoScrollRef = useRef(true)

  const rowVirtualizer = useVirtualizer({
    count: terminalEntries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 22,
    overscan: 20,
  })

  /* Auto-scroll al fondo cuando llegan nuevas entradas */
  useEffect(() => {
    if (autoScrollRef.current && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'auto' })
    }
  }, [terminalEntries.length])

  const handleScrollToBottom = () => {
    autoScrollRef.current = true
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div
      className="flex flex-col rounded border"
      style={{
        backgroundColor: '#0a0e1a',
        borderColor: '#1f2937',
        height: '60vh',
        minHeight: '400px',
      }}
    >
      {/* ── Barra superior ── */}
      <div
        className="flex items-center justify-between px-4 py-2 border-b"
        style={{
          borderColor: '#1f2937',
          backgroundColor: '#111827',
          borderRadius: '8px 8px 0 0',
        }}
      >
        <div className="flex items-center gap-2">
          <Terminal size={14} style={{ color: '#00ff88' }} />
          <span
            className="text-xs font-bold tracking-widest"
            style={{ color: '#00ff88' }}
          >
            TERMINAL
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded font-mono"
            style={{ backgroundColor: '#1f2937', color: '#4b5563' }}
          >
            {terminalEntries.length} líneas
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleScrollToBottom}
            title="Ir al final"
            className="flex items-center gap-1 text-xs px-2 py-1 rounded"
            style={{
              color: '#6b7280',
              backgroundColor: 'transparent',
              fontFamily: 'inherit',
              cursor: 'pointer',
              border: '1px solid #1f2937',
            }}
          >
            <ChevronDown size={12} />
            FIN
          </button>
          <button
            onClick={clearTerminal}
            title="Limpiar terminal"
            className="flex items-center gap-1 text-xs px-2 py-1 rounded"
            style={{
              color: '#6b7280',
              backgroundColor: 'transparent',
              fontFamily: 'inherit',
              cursor: 'pointer',
              border: '1px solid #1f2937',
            }}
          >
            <Trash2 size={12} />
            LIMPIAR
          </button>
        </div>
      </div>

      {/* ── Cuerpo del terminal (virtualizado) ── */}
      {terminalEntries.length === 0 ? (
        <div
          className="flex-1 flex flex-col items-center justify-center gap-2"
          style={{ color: '#374151' }}
        >
          <Terminal size={24} />
          <span className="text-xs font-mono">
            Esperando actividad del agente...
          </span>
          <span className="text-xs font-mono" style={{ color: '#1f2937' }}>
            Inicia un scan para ver los comandos aquí
          </span>
        </div>
      ) : (
        <div
          ref={parentRef}
          className="flex-1 overflow-y-auto"
          style={{ fontFamily: 'monospace' }}
          onScroll={(e) => {
            const el = e.currentTarget
            const atBottom =
              el.scrollHeight - el.scrollTop - el.clientHeight < 40
            autoScrollRef.current = atBottom
          }}
        >
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((vItem) => {
              const entry = terminalEntries[vItem.index]
              return (
                <div
                  key={vItem.key}
                  data-index={vItem.index}
                  ref={rowVirtualizer.measureElement}
                  style={{
                    position: 'absolute',
                    top: vItem.start,
                    left: 0,
                    right: 0,
                  }}
                >
                  <TerminalLine entry={entry} />
                </div>
              )
            })}
          </div>
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}
