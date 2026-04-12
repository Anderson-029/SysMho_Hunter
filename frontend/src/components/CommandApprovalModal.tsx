/**
 * CommandApprovalModal — modal que aparece automáticamente cuando SysMho Hunter
 * necesita ejecutar una herramienta y requiere aprobación de Anderson.
 *
 * Muestra:
 * - El comando exacto que se va a ejecutar
 * - Explicación en lenguaje natural (qué hace, por qué lo necesita)
 * - Nivel de riesgo con color
 * - Botones Aprobar / Rechazar
 */
import { motion, AnimatePresence } from 'framer-motion'
import {
  Terminal,
  CheckCircle,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
} from 'lucide-react'
import { toast } from 'sonner'
import { useScanStore } from '../stores/scanStore'

const RISK_COLOR: Record<string, string> = {
  critical: '#ff3366',
  high: '#f97316',
  medium: '#ffd700',
  low: '#00bfff',
}

const RISK_LABEL: Record<string, string> = {
  critical: 'CRÍTICO',
  high: 'ALTO',
  medium: 'MEDIO',
  low: 'BAJO',
}

export function CommandApprovalModal() {
  const { pendingCommandRequest, reviewAction, clearPendingCommandRequest } =
    useScanStore()

  const req = pendingCommandRequest
  if (!req) return null

  const riskColor = RISK_COLOR[req.risk_level] ?? '#6b7280'
  const riskLabel = RISK_LABEL[req.risk_level] ?? req.risk_level.toUpperCase()

  const handleApprove = async () => {
    clearPendingCommandRequest()
    await reviewAction(req.action_id, 'approved')
    toast.success(`${req.tool_name} aprobado`, {
      description: 'El agente ejecutará el comando.',
    })
  }

  const handleReject = async () => {
    clearPendingCommandRequest()
    await reviewAction(req.action_id, 'rejected')
    toast.error(`${req.tool_name} rechazado`, {
      description: 'El agente omitirá esta herramienta.',
    })
  }

  return (
    <AnimatePresence>
      <motion.div
        key="overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '16px',
        }}
      >
        <motion.div
          key="modal"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.18 }}
          style={{
            backgroundColor: '#111827',
            border: `1px solid ${riskColor}80`,
            borderRadius: '8px',
            width: '100%',
            maxWidth: '560px',
            fontFamily: 'inherit',
          }}
        >
          {/* ── CABECERA ── */}
          <div
            className="flex items-center gap-3 px-5 py-4 border-b"
            style={{ borderColor: '#1f2937' }}
          >
            <Terminal size={18} style={{ color: riskColor }} />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span
                  className="text-sm font-bold tracking-wide"
                  style={{ color: '#e5e7eb' }}
                >
                  ACCIÓN REQUERIDA —{' '}
                  <span style={{ color: '#00bfff' }}>
                    {req.tool_name.toUpperCase()}
                  </span>
                </span>
              </div>
              <div className="flex items-center gap-1.5 mt-1">
                <ShieldAlert size={11} style={{ color: riskColor }} />
                <span
                  className="text-xs font-bold"
                  style={{ color: riskColor }}
                >
                  RIESGO {riskLabel}
                </span>
              </div>
            </div>
          </div>

          <div className="px-5 py-4 space-y-4">
            {/* ── COMANDO ── */}
            <div>
              <div
                className="text-xs font-bold mb-1.5 flex items-center gap-1.5"
                style={{ color: '#6b7280' }}
              >
                <Terminal size={11} />
                COMANDO A EJECUTAR
              </div>
              <div
                className="text-xs font-mono px-3 py-2.5 rounded"
                style={{
                  backgroundColor: '#0a0e1a',
                  color: '#00ff88',
                  border: '1px solid #1f2937',
                  wordBreak: 'break-all',
                }}
              >
                <span style={{ color: '#4b5563', userSelect: 'none' }}>
                  ${' '}
                </span>
                {req.command}
              </div>
            </div>

            {/* ── QUÉ VA A HACER ── */}
            {req.human_explanation && (
              <div>
                <div
                  className="text-xs font-bold mb-1.5 flex items-center gap-1.5"
                  style={{ color: '#6b7280' }}
                >
                  <HelpCircle size={11} />
                  ¿QUÉ VA A HACER?
                </div>
                <p className="text-sm" style={{ color: '#d1d5db', lineHeight: 1.6 }}>
                  {req.human_explanation}
                </p>
              </div>
            )}

            {/* ── POR QUÉ LO NECESITA ── */}
            {req.why_needed && (
              <div>
                <div
                  className="text-xs font-bold mb-1.5 flex items-center gap-1.5"
                  style={{ color: '#6b7280' }}
                >
                  <AlertTriangle size={11} />
                  ¿POR QUÉ LO NECESITO?
                </div>
                <p className="text-sm" style={{ color: '#9ca3af', lineHeight: 1.6 }}>
                  {req.why_needed}
                </p>
              </div>
            )}

            {/* ── RIESGO ── */}
            {req.risk_explanation && (
              <div
                className="flex items-start gap-2 text-xs px-3 py-2.5 rounded"
                style={{
                  backgroundColor: riskColor + '15',
                  border: `1px solid ${riskColor}40`,
                  color: riskColor,
                }}
              >
                <ShieldAlert size={13} style={{ flexShrink: 0, marginTop: 1 }} />
                <span style={{ lineHeight: 1.5 }}>{req.risk_explanation}</span>
              </div>
            )}
          </div>

          {/* ── BOTONES ── */}
          <div
            className="flex gap-3 px-5 py-4 border-t"
            style={{ borderColor: '#1f2937' }}
          >
            <button
              onClick={handleApprove}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded text-sm font-bold"
              style={{
                backgroundColor: '#00ff88',
                color: '#0a0e1a',
                fontFamily: 'inherit',
                cursor: 'pointer',
              }}
            >
              <CheckCircle size={14} />
              APROBAR
            </button>
            <button
              onClick={handleReject}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded text-sm font-bold border"
              style={{
                borderColor: '#ff3366',
                color: '#ff3366',
                backgroundColor: 'transparent',
                fontFamily: 'inherit',
                cursor: 'pointer',
              }}
            >
              <XCircle size={14} />
              RECHAZAR
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
