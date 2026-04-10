import { useRef, useState, useEffect, useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Trash2, PauseCircle, PlayCircle, ArrowDownCircle } from 'lucide-react'
import { useScanStore } from '../stores/scanStore'

const LEVEL_COLOR: Record<string, string> = {
  debug: '#6b7280',
  info: '#00bfff',
  warning: '#ffd700',
  error: '#ff3366',
  critical: '#ff3366',
  success: '#00ff88',
}

const LEVEL_BG: Record<string, string> = {
  error: 'rgba(255,51,102,0.05)',
  critical: 'rgba(255,51,102,0.05)',
  warning: 'rgba(255,215,0,0.03)',
}

export function LiveLogs() {
  const { logs, wsConnected } = useScanStore()
  const parentRef = useRef<HTMLDivElement>(null)
  const [paused, setPaused] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [frozenLogs, setFrozenLogs] = useState(logs)

  // Cuando no está pausado, mantener logs actualizados
  useEffect(() => {
    if (!paused) setFrozenLogs(logs)
  }, [logs, paused])

  const displayLogs = paused ? frozenLogs : logs

  const virtualizer = useVirtualizer({
    count: displayLogs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 24,
    overscan: 20,
  })

  // Auto-scroll al último log
  useEffect(() => {
    if (autoScroll && !paused && displayLogs.length > 0) {
      virtualizer.scrollToIndex(displayLogs.length - 1, { behavior: 'smooth' })
    }
  }, [displayLogs.length, autoScroll, paused]) // eslint-disable-line

  const levelCounts = useMemo(
    () => ({
      error: displayLogs.filter(
        l => l.log_level === 'error' || l.log_level === 'critical',
      ).length,
      warning: displayLogs.filter(l => l.log_level === 'warning').length,
      info: displayLogs.filter(
        l => l.log_level === 'info' || l.log_level === 'success',
      ).length,
    }),
    [displayLogs],
  )

  const handleClear = () => {
    setFrozenLogs([])
    // Limpia también el store (resetea sin reconectar WS)
    useScanStore.setState({ logs: [] })
  }

  return (
    <div className="space-y-2">
      {/* Barra de controles */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Indicador WS */}
          <div
            className="flex items-center gap-1.5 text-xs"
            style={{ color: wsConnected ? '#00ff88' : '#ff3366' }}
          >
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${wsConnected ? 'animate-pulse' : ''}`}
              style={{
                backgroundColor: wsConnected ? '#00ff88' : '#ff3366',
              }}
            />
            {wsConnected ? 'LIVE' : 'OFFLINE'}
          </div>
          {/* Badges de conteo */}
          {levelCounts.error > 0 && (
            <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'rgba(255,51,102,0.15)', color: '#ff3366' }}>
              ERR {levelCounts.error}
            </span>
          )}
          {levelCounts.warning > 0 && (
            <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'rgba(255,215,0,0.1)', color: '#ffd700' }}>
              WARN {levelCounts.warning}
            </span>
          )}
          <span className="text-xs" style={{ color: '#4b5563' }}>
            {displayLogs.length} logs
          </span>
        </div>

        {/* Botones de control */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => { setAutoScroll(true); virtualizer.scrollToIndex(displayLogs.length - 1) }}
            title="Ir al final"
            className="p-1 rounded"
            style={{ color: autoScroll ? '#00ff88' : '#4b5563' }}
          >
            <ArrowDownCircle size={14} />
          </button>
          <button
            onClick={() => setPaused(p => !p)}
            title={paused ? 'Reanudar' : 'Pausar'}
            className="p-1 rounded"
            style={{ color: paused ? '#ffd700' : '#6b7280' }}
          >
            {paused ? <PlayCircle size={14} /> : <PauseCircle size={14} />}
          </button>
          <button
            onClick={handleClear}
            title="Limpiar logs"
            className="p-1 rounded"
            style={{ color: '#6b7280' }}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Contenedor del terminal virtual */}
      <div
        ref={parentRef}
        className="rounded border font-mono text-xs overflow-auto"
        style={{
          backgroundColor: '#0a0e1a',
          borderColor: '#1f2937',
          height: '480px',
        }}
      >
        {displayLogs.length === 0 && (
          <div
            className="flex items-center justify-center h-full"
            style={{ color: '#374151' }}
          >
            Esperando logs del sistema...
          </div>
        )}

        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            position: 'relative',
          }}
        >
          {virtualizer.getVirtualItems().map(virtualRow => {
            const log = displayLogs[virtualRow.index]
            return (
              <div
                key={virtualRow.index}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualRow.start}px)`,
                  height: `${virtualRow.size}px`,
                  backgroundColor: LEVEL_BG[log.log_level] || 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '0 10px',
                  boxSizing: 'border-box',
                }}
              >
                <span style={{ color: '#374151', minWidth: '58px', flexShrink: 0 }}>
                  {log.created_at ? log.created_at.slice(11, 19) : '--:--:--'}
                </span>
                <span
                  style={{
                    color: LEVEL_COLOR[log.log_level] ?? '#6b7280',
                    minWidth: '52px',
                    fontWeight: 700,
                    flexShrink: 0,
                  }}
                >
                  {log.log_level.toUpperCase()}
                </span>
                {log.component && (
                  <span style={{ color: '#9333ea', minWidth: '70px', flexShrink: 0 }}>
                    [{log.component}]
                  </span>
                )}
                <span
                  style={{
                    color: '#d1d5db',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {log.message}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
