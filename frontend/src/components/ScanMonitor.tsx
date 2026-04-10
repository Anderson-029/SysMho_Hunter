import { useState } from 'react'
import { motion } from 'framer-motion'
import { Play, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'
import { useScanStore } from '../stores/scanStore'

const STATUS_COLORS: Record<string, string> = {
  pending: '#6b7280',
  running: '#00ff88',
  completed: '#00bfff',
  failed: '#ff3366',
  cancelled: '#ffd700',
}

const PHASE_PROGRESS: Record<string, number> = {
  recon: 20,
  port_scan: 35,
  dir_fuzz: 50,
  vuln_scan: 65,
  exploit_check: 80,
  analyzing: 85,
  brain: 92,
  report: 96,
  completed: 100,
}

export function ScanMonitor() {
  const { scans, targets, startScan } = useScanStore()
  const [selectedTarget, setSelectedTarget] = useState('')
  const [scanType, setScanType] = useState('full')
  const [launching, setLaunching] = useState(false)

  const handleStart = async () => {
    if (!selectedTarget) return
    setLaunching(true)
    await startScan(selectedTarget, scanType)
    setLaunching(false)
  }

  const getTarget = (targetId: string) => targets.find(t => t.id === targetId)

  const formatDate = (iso: string) => {
    try {
      return formatDistanceToNow(new Date(iso), { addSuffix: true, locale: es })
    } catch {
      return iso.slice(0, 16)
    }
  }

  return (
    <div className="space-y-4">
      {/* Iniciar scan */}
      <div
        className="rounded border p-4 space-y-3"
        style={{ backgroundColor: '#111827', borderColor: '#1f2937' }}
      >
        <h3
          className="text-xs font-bold tracking-widest"
          style={{ color: '#00ff88' }}
        >
          ▶ INICIAR SCAN
        </h3>
        <div className="flex gap-3">
          <select
            value={selectedTarget}
            onChange={e => setSelectedTarget(e.target.value)}
            className="flex-1 rounded px-3 py-2 text-sm"
            style={{
              backgroundColor: '#0a0e1a',
              color: '#e5e7eb',
              border: '1px solid #1f2937',
              fontFamily: 'inherit',
            }}
          >
            <option value="">Seleccionar target...</option>
            {targets.map(t => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <select
            value={scanType}
            onChange={e => setScanType(e.target.value)}
            className="rounded px-3 py-2 text-sm"
            style={{
              backgroundColor: '#0a0e1a',
              color: '#e5e7eb',
              border: '1px solid #1f2937',
              fontFamily: 'inherit',
            }}
          >
            <option value="full">Full</option>
            <option value="recon">Recon</option>
            <option value="vuln_scan">Vuln Scan</option>
          </select>
          <button
            onClick={handleStart}
            disabled={!selectedTarget || launching}
            className="px-4 py-2 rounded text-sm font-bold flex items-center gap-2"
            style={{
              backgroundColor: selectedTarget ? '#00ff88' : '#1f2937',
              color: selectedTarget ? '#0a0e1a' : '#4b5563',
              cursor: selectedTarget ? 'pointer' : 'not-allowed',
              fontFamily: 'inherit',
              transition: 'background-color 0.2s',
            }}
          >
            {launching ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Play size={14} />
            )}
            INICIAR
          </button>
        </div>
      </div>

      {/* Lista de scans */}
      <div className="space-y-2">
        {scans.length === 0 && (
          <div
            className="text-center py-10 text-xs"
            style={{ color: '#4b5563' }}
          >
            No hay scans. Selecciona un target e inicia uno arriba.
          </div>
        )}
        {scans.map(scan => {
          const target = getTarget(scan.target_id)
          const isRunning = scan.status === 'running'
          const progress = scan.phase ? (PHASE_PROGRESS[scan.phase] ?? 10) : 0
          const statusColor = STATUS_COLORS[scan.status] || '#6b7280'

          return (
            <div
              key={scan.id}
              className="rounded border p-3"
              style={{
                backgroundColor: '#111827',
                borderColor: isRunning ? '#00ff881a' : '#1f2937',
              }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div
                    className="text-sm font-medium"
                    style={{ color: '#e5e7eb' }}
                  >
                    {target?.name || scan.target_id.slice(0, 8)}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: '#6b7280' }}>
                    {scan.scan_type}
                    {scan.phase ? ` · fase: ${scan.phase}` : ''}
                    {' · '}
                    {formatDate(scan.created_at)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isRunning && (
                    <span
                      className="animate-pulse text-xs"
                      style={{ color: '#00ff88' }}
                    >
                      ●
                    </span>
                  )}
                  <span
                    className="text-xs px-2 py-0.5 rounded font-bold"
                    style={{
                      color: statusColor,
                      border: `1px solid ${statusColor}`,
                      fontFamily: 'inherit',
                    }}
                  >
                    {scan.status.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Progress bar — solo cuando está en ejecución */}
              {isRunning && scan.phase && (
                <div
                  className="mt-2 rounded-full overflow-hidden"
                  style={{ height: '3px', backgroundColor: '#1f2937' }}
                >
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    style={{
                      height: '100%',
                      backgroundColor: '#00ff88',
                      borderRadius: '999px',
                    }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
