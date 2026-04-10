import { useState } from 'react'
import { toast } from 'sonner'
import { ShieldAlert, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { useScanStore } from '../stores/scanStore'

const RISK_COLOR: Record<string, string> = {
  critical: '#ff3366',
  high: '#f97316',
  medium: '#ffd700',
  low: '#00bfff',
}

export function PendingActions() {
  const { pendingActions, reviewAction } = useScanStore()
  const [confirmId, setConfirmId] = useState<string | null>(null)

  const handleApprove = async (id: string) => {
    await reviewAction(id, 'approved')
    toast.success('Acción aprobada', {
      description: 'El agente ejecutará la acción autorizada.',
    })
  }

  const handleReject = async (id: string) => {
    await reviewAction(id, 'rejected')
    toast.error('Acción rechazada', {
      description: 'El agente buscará alternativas de menor riesgo.',
    })
  }

  const handleApproveClick = (id: string, riskLevel: string) => {
    if (riskLevel === 'critical') {
      setConfirmId(id)
    } else {
      handleApprove(id)
    }
  }

  if (pendingActions.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center py-12 gap-2"
        style={{ color: '#4b5563' }}
      >
        <CheckCircle size={28} style={{ color: '#00ff8840' }} />
        <span className="text-xs">No hay acciones pendientes de aprobación.</span>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Aviso de seguridad */}
      <div
        className="flex items-center gap-2 text-xs p-3 rounded"
        style={{ backgroundColor: '#1f2937', color: '#ffd700' }}
      >
        <AlertTriangle size={14} />
        <span>
          Estas acciones requieren tu aprobación antes de ejecutarse. Revisa
          el riesgo antes de aprobar.
        </span>
      </div>

      {pendingActions.map(action => {
        const riskColor = RISK_COLOR[action.risk_level] || '#6b7280'
        const isCritical = action.risk_level === 'critical'

        return (
          <div
            key={action.id}
            className="rounded border p-4"
            style={{
              backgroundColor: '#111827',
              borderColor: riskColor + '60',
            }}
          >
            <div className="flex items-start gap-3 mb-3">
              <ShieldAlert
                size={16}
                style={{ color: riskColor, flexShrink: 0, marginTop: 2 }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded ${isCritical ? 'animate-pulse-border' : ''}`}
                    style={{
                      color: riskColor,
                      border: `1px solid ${riskColor}`,
                    }}
                  >
                    RIESGO {action.risk_level.toUpperCase()}
                  </span>
                  <span
                    className="text-xs font-mono"
                    style={{ color: '#00bfff' }}
                  >
                    {action.action_type}
                  </span>
                </div>
                <div className="text-sm" style={{ color: '#e5e7eb' }}>
                  {action.description}
                </div>
                {action.risk_reason && (
                  <div
                    className="text-xs mt-1"
                    style={{ color: '#6b7280' }}
                  >
                    {action.risk_reason}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleApproveClick(action.id, action.risk_level)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold"
                style={{
                  backgroundColor: '#00ff88',
                  color: '#0a0e1a',
                  fontFamily: 'inherit',
                }}
              >
                <CheckCircle size={12} />
                APROBAR
              </button>
              <button
                onClick={() => handleReject(action.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold border"
                style={{
                  borderColor: '#ff3366',
                  color: '#ff3366',
                  backgroundColor: 'transparent',
                  fontFamily: 'inherit',
                }}
              >
                <XCircle size={12} />
                RECHAZAR
              </button>
            </div>
          </div>
        )
      })}

      {/* Modal de confirmación para acciones críticas */}
      {confirmId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
          }}
        >
          <div
            className="rounded border p-6"
            style={{
              backgroundColor: '#111827',
              borderColor: '#ff3366',
              maxWidth: '400px',
              width: '90%',
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <ShieldAlert size={20} style={{ color: '#ff3366' }} />
              <h3
                className="text-sm font-bold"
                style={{ color: '#ff3366', fontFamily: 'inherit' }}
              >
                CONFIRMAR ACCIÓN CRÍTICA
              </h3>
            </div>
            <p className="text-xs mb-5" style={{ color: '#9ca3af' }}>
              Esta acción tiene nivel de riesgo CRÍTICO. Una vez aprobada, el
              agente la ejecutará de forma autónoma. ¿Confirmas?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  handleApprove(confirmId)
                  setConfirmId(null)
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded text-xs font-bold"
                style={{
                  backgroundColor: '#ff3366',
                  color: '#fff',
                  fontFamily: 'inherit',
                }}
              >
                <CheckCircle size={12} />
                CONFIRMAR
              </button>
              <button
                onClick={() => setConfirmId(null)}
                className="px-4 py-2 rounded text-xs border"
                style={{
                  borderColor: '#374151',
                  color: '#6b7280',
                  backgroundColor: 'transparent',
                  fontFamily: 'inherit',
                }}
              >
                CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
