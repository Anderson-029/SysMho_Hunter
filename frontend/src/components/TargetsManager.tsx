import { useEffect, useState } from 'react'
import type { Target, BountyTierTable } from '../types'
import {
  Plus,
  Trash2,
  ExternalLink,
  Shield,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Zap,
  Clock,
  Target as TargetIcon,
} from 'lucide-react'
import { TargetForm } from './TargetForm'
import { ScopeImporter } from './ScopeImporter'

const SEV_COLORS: Record<string, string> = {
  low: 'text-green-400',
  medium: 'text-yellow-400',
  high: 'text-orange-400',
  critical: 'text-red-400',
}

function BountyTierView({
  label,
  tier,
}: {
  label: string
  tier: BountyTierTable
}) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 mb-1">{label}</p>
      <div className="grid grid-cols-4 gap-2">
        {(['low', 'medium', 'high', 'critical'] as const).map(sev => {
          const r = tier[sev]
          if (!r?.min && !r?.max) return null
          return (
            <div
              key={sev}
              className="bg-gray-800 border border-gray-700 rounded p-2 text-center"
            >
              <p className={`text-xs capitalize mb-1 ${SEV_COLORS[sev]}`}>
                {sev}
              </p>
              <p className="text-sm font-bold text-white">
                ${r.min?.toLocaleString()}
                {r.max && r.max !== r.min ? `–${r.max?.toLocaleString()}` : ''}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function TargetsManager() {
  const [targets, setTargets] = useState<Target[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [showImporter, setShowImporter] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    loadTargets()
  }, [])

  const loadTargets = async () => {
    try {
      const { api } = await import('../api/client')
      const data = await api.get('/targets/')
      setTargets(data)
    } catch (err) {
      console.error('Error loading targets:', err)
    }
  }

  const handleCreateTarget = async (data: Partial<Target>) => {
    setIsLoading(true)
    try {
      const { api } = await import('../api/client')
      await api.post('/targets/', { ...data, scopes: [] })
      setShowForm(false)
      loadTargets()
    } catch (err) {
      console.error('Error creating target:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteTarget = async (id: string) => {
    if (!confirm('¿Eliminar este programa?')) return
    try {
      const { api } = await import('../api/client')
      await api.delete(`/targets/${id}`)
      loadTargets()
    } catch (err) {
      console.error('Error deleting target:', err)
    }
  }

  const handleDeleteScope = async (targetId: string, scopeId: string) => {
    try {
      const { api } = await import('../api/client')
      await api.delete(`/targets/${targetId}/scopes/${scopeId}`)
      loadTargets()
    } catch (err) {
      console.error('Error deleting scope:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Programas</h1>
          <p className="text-gray-400 mt-1">
            {targets.length} programa{targets.length !== 1 ? 's' : ''}{' '}
            configurado{targets.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
        >
          <Plus size={20} />
          Nuevo Programa
        </button>
      </div>

      {/* Lista */}
      <div className="space-y-4">
        {targets.length === 0 ? (
          <div className="text-center py-12 border border-gray-700 rounded-lg bg-gray-900">
            <TargetIcon size={40} className="mx-auto text-gray-600 mb-3" />
            <p className="text-gray-400">
              Sin programas. Crea uno para empezar.
            </p>
          </div>
        ) : (
          targets.map(target => (
            <div
              key={target.id}
              className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden hover:border-gray-600 transition"
            >
              {/* Card header */}
              <button
                onClick={() =>
                  setExpandedId(expandedId === target.id ? null : target.id)
                }
                className="w-full p-4 flex items-start justify-between hover:bg-gray-800/50 transition text-left"
              >
                <div className="flex-1 space-y-2">
                  {/* Nombre + badges */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-lg font-semibold text-white">
                      {target.name}
                    </h3>
                    {target.platform && (
                      <span className="px-2 py-0.5 text-xs rounded bg-blue-900/40 border border-blue-700 text-blue-300">
                        {target.platform}
                      </span>
                    )}
                    {target.safe_harbor ? (
                      <Shield size={14} className="text-green-500" />
                    ) : (
                      <AlertTriangle size={14} className="text-yellow-500" />
                    )}
                    {target.active_campaign && (
                      <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded bg-orange-900/40 border border-orange-700 text-orange-300">
                        <Zap size={11} />
                        Campaign activa
                      </span>
                    )}
                  </div>

                  {/* Stats rápidas */}
                  <div className="flex items-center gap-4 text-xs text-gray-400 flex-wrap">
                    <span>{target.scopes.length} scopes</span>
                    {target.organization && <span>{target.organization}</span>}
                    {target.response_efficiency_pct != null && (
                      <span className="text-green-400">
                        ⚡ {target.response_efficiency_pct}% efficiency
                      </span>
                    )}
                    {target.avg_response_hours != null && (
                      <span className="flex items-center gap-1">
                        <Clock size={11} />
                        {target.avg_response_hours}h response
                      </span>
                    )}
                    {target.bounty_tiers?.primary?.critical?.max != null && (
                      <span className="text-red-400 font-medium">
                        Critical: up to $
                        {target.bounty_tiers.primary.critical.max.toLocaleString()}
                      </span>
                    )}
                  </div>

                  {/* Focus areas chips */}
                  {target.focus_areas && target.focus_areas.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {target.focus_areas.slice(0, 5).map(area => (
                        <span
                          key={area}
                          className="px-2 py-0.5 text-xs rounded bg-red-900/20 border border-red-800 text-red-300"
                        >
                          {area}
                        </span>
                      ))}
                      {target.focus_areas.length > 5 && (
                        <span className="text-xs text-gray-500">
                          +{target.focus_areas.length - 5} más
                        </span>
                      )}
                    </div>
                  )}

                  {/* Program tags */}
                  {target.program_tags && target.program_tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {target.program_tags.map(tag => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 text-xs rounded bg-gray-800 border border-gray-600 text-gray-300"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 ml-4 shrink-0">
                  {target.program_url && (
                    <a
                      href={target.program_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={e => e.stopPropagation()}
                      className="p-2 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition"
                    >
                      <ExternalLink size={16} />
                    </a>
                  )}
                  {expandedId === target.id ? (
                    <ChevronUp size={20} className="text-gray-500" />
                  ) : (
                    <ChevronDown size={20} className="text-gray-500" />
                  )}
                </div>
              </button>

              {/* Contenido expandido */}
              {expandedId === target.id && (
                <div className="border-t border-gray-700 p-5 space-y-5 bg-gray-950">

                  {/* Campaña activa */}
                  {target.active_campaign && (
                    <div className="p-3 rounded border border-orange-700 bg-orange-900/10">
                      <p className="text-sm font-semibold text-orange-300 mb-1 flex items-center gap-1">
                        <Zap size={14} /> Campaña Activa
                        {target.active_campaign.end_date && (
                          <span className="text-xs text-orange-400 font-normal ml-2">
                            — termina {target.active_campaign.end_date}
                          </span>
                        )}
                      </p>
                      {target.active_campaign.description && (
                        <p className="text-xs text-gray-300">
                          {target.active_campaign.description}
                        </p>
                      )}
                      {target.active_campaign.bounty_multipliers && (
                        <div className="flex gap-3 mt-2 flex-wrap">
                          {Object.entries(
                            target.active_campaign.bounty_multipliers
                          ).map(([sev, mul]) =>
                            mul != null ? (
                              <span
                                key={sev}
                                className={`text-xs font-medium ${SEV_COLORS[sev]}`}
                              >
                                {sev}: {mul}x
                              </span>
                            ) : null
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Bounty Tiers */}
                  {target.bounty_tiers?.primary && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-semibold text-gray-300">
                        💰 Recompensas
                      </h4>
                      <BountyTierView
                        label="Primary Targets"
                        tier={target.bounty_tiers.primary}
                      />
                      {target.bounty_tiers.secondary && (
                        <BountyTierView
                          label="Secondary Targets"
                          tier={target.bounty_tiers.secondary}
                        />
                      )}
                    </div>
                  )}

                  {/* Timing stats */}
                  {(target.avg_response_hours != null ||
                    target.avg_triage_hours != null) && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">
                        ⏱️ Tiempos de Respuesta
                      </h4>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {[
                          ['First Response', target.avg_response_hours],
                          ['Triage', target.avg_triage_hours],
                          ['Bounty', target.avg_bounty_hours],
                          ['Resolution', target.avg_resolution_hours],
                        ].map(([label, val]) =>
                          val != null ? (
                            <div
                              key={label as string}
                              className="bg-gray-800 border border-gray-700 rounded p-2 text-center"
                            >
                              <p className="text-xs text-gray-400">
                                {label as string}
                              </p>
                              <p className="text-sm font-bold text-white">
                                {(val as number) >= 24
                                  ? `${Math.round((val as number) / 24)}d`
                                  : `${val}h`}
                              </p>
                            </div>
                          ) : null
                        )}
                      </div>
                    </div>
                  )}

                  {/* Reglas */}
                  {target.rules_md && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">
                        Reglas del Programa
                      </h4>
                      <pre className="bg-gray-800 border border-gray-700 rounded p-3 text-xs text-gray-300 overflow-x-auto max-h-40 overflow-y-auto whitespace-pre-wrap">
                        {target.rules_md}
                      </pre>
                    </div>
                  )}

                  {/* Out of scope */}
                  {target.out_of_scope_notes && (
                    <div>
                      <h4 className="text-sm font-semibold text-yellow-400 mb-1">
                        ⚠️ Out of Scope
                      </h4>
                      <p className="bg-yellow-900/20 border border-yellow-700 rounded p-2 text-sm text-yellow-100">
                        {target.out_of_scope_notes}
                      </p>
                    </div>
                  )}

                  {/* Scopes */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-sm font-semibold text-gray-300">
                        Scopes ({target.scopes.length})
                      </h4>
                      <button
                        onClick={() => setShowImporter(target.id)}
                        className="text-xs px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition"
                      >
                        + Importar
                      </button>
                    </div>
                    <div className="space-y-1.5 max-h-60 overflow-y-auto">
                      {target.scopes.map(scope => (
                        <div
                          key={scope.id}
                          className="flex items-center justify-between p-2 bg-gray-800 border border-gray-700 rounded text-sm"
                        >
                          <div className="flex items-center gap-2 flex-1">
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-mono ${
                                scope.is_in_scope
                                  ? 'bg-green-900/30 text-green-300'
                                  : 'bg-red-900/30 text-red-300'
                              }`}
                            >
                              {scope.scope_type}
                            </span>
                            {scope.tier && (
                              <span className="px-1.5 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
                                {scope.tier}
                              </span>
                            )}
                            <code className="text-gray-300 text-xs">
                              {scope.value}
                            </code>
                          </div>
                          <button
                            onClick={() =>
                              handleDeleteScope(target.id, scope.id)
                            }
                            className="p-1 hover:bg-red-900/20 rounded text-gray-500 hover:text-red-400 transition"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Eliminar */}
                  <button
                    onClick={() => handleDeleteTarget(target.id)}
                    className="w-full px-4 py-2 bg-red-900/20 hover:bg-red-900/40 text-red-400 border border-red-800 rounded transition flex items-center justify-center gap-2 text-sm"
                  >
                    <Trash2 size={16} />
                    Eliminar Programa
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Modales */}
      {showForm && (
        <TargetForm
          onSubmit={handleCreateTarget}
          onClose={() => setShowForm(false)}
          isLoading={isLoading}
        />
      )}
      {showImporter && (
        <ScopeImporter
          targetId={showImporter}
          onClose={() => setShowImporter(null)}
          onSuccess={loadTargets}
        />
      )}
    </div>
  )
}
