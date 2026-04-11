import { useEffect, useState } from 'react'
import type { Target } from '../types'
import {
  Plus,
  Trash2,
  ExternalLink,
  Shield,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { TargetForm } from './TargetForm'
import { ScopeImporter } from './ScopeImporter'

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
      const response = await fetch('http://localhost:8000/api/v1/targets/')
      if (response.ok) {
        const data = await response.json()
        setTargets(data)
      }
    } catch (err) {
      console.error('Error loading targets:', err)
    }
  }

  const handleCreateTarget = async (targetData: Partial<Target>) => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/v1/targets/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...targetData,
          scopes: [],
        }),
      })

      if (response.ok) {
        setShowForm(false)
        loadTargets()
      }
    } catch (err) {
      console.error('Error creating target:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteTarget = async (id: string) => {
    if (!confirm('¿Eliminar este programa?')) return

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/targets/${id}`,
        { method: 'DELETE' }
      )

      if (response.ok) {
        loadTargets()
      }
    } catch (err) {
      console.error('Error deleting target:', err)
    }
  }

  const handleDeleteScope = async (targetId: string, scopeId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/targets/${targetId}/scopes/${scopeId}`,
        { method: 'DELETE' }
      )

      if (response.ok) {
        loadTargets()
      }
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
            {targets.length} programa{targets.length !== 1 ? 's' : ''} configurado
            {targets.length !== 1 ? 's' : ''}
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

      {/* Lista de targets */}
      <div className="space-y-4">
        {targets.length === 0 ? (
          <div className="text-center py-12 border border-gray-700 rounded-lg bg-gray-900">
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
              {/* Header del target */}
              <button
                onClick={() =>
                  setExpandedId(expandedId === target.id ? null : target.id)
                }
                className="w-full p-4 flex items-center justify-between hover:bg-gray-800/50 transition"
              >
                <div className="flex items-center gap-4 flex-1 text-left">
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      {target.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1 text-sm text-gray-400">
                      <span>{target.platform || 'manual'}</span>
                      {target.safe_harbor && (
                        <Shield size={14} className="text-green-500" />
                      )}
                      {!target.safe_harbor && (
                        <AlertTriangle
                          size={14}
                          className="text-yellow-500"
                        />
                      )}
                      <span>•</span>
                      <span>{target.scopes.length} scopes</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {target.program_url && (
                    <a
                      href={target.program_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={e => e.stopPropagation()}
                      className="p-2 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition"
                    >
                      <ExternalLink size={18} />
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
                <div className="border-t border-gray-700 p-4 space-y-4 bg-gray-950">
                  {/* Reglas */}
                  {target.rules_md && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">
                        Reglas del Programa
                      </h4>
                      <pre className="bg-gray-800 border border-gray-700 rounded p-3 text-xs text-gray-300 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap break-words">
                        {target.rules_md}
                      </pre>
                    </div>
                  )}

                  {/* Out of scope */}
                  {target.out_of_scope_notes && (
                    <div>
                      <h4 className="text-sm font-semibold text-yellow-400 mb-2">
                        ⚠️ Out of Scope
                      </h4>
                      <p className="bg-yellow-900/20 border border-yellow-700 rounded p-2 text-sm text-yellow-100">
                        {target.out_of_scope_notes}
                      </p>
                    </div>
                  )}

                  {/* Bounty table */}
                  {target.bounty_table && Object.keys(target.bounty_table).length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">
                        💰 Tabla de Recompensas
                      </h4>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {Object.entries(target.bounty_table).map(
                          ([level, amount]) => (
                            <div
                              key={level}
                              className="bg-gray-800 border border-gray-700 rounded p-3 text-center"
                            >
                              <p className="text-xs text-gray-400 capitalize">
                                {level}
                              </p>
                              <p className="text-lg font-bold text-white">
                                {amount}
                              </p>
                            </div>
                          )
                        )}
                      </div>
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
                        className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition"
                      >
                        + Importar
                      </button>
                    </div>

                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {target.scopes.map(scope => (
                        <div
                          key={scope.id}
                          className="flex items-center justify-between p-2 bg-gray-800 border border-gray-700 rounded text-sm"
                        >
                          <div className="flex items-center gap-2 flex-1">
                            <span
                              className={`px-2 py-1 rounded text-xs font-mono ${
                                scope.is_in_scope
                                  ? 'bg-green-900/30 text-green-300'
                                  : 'bg-red-900/30 text-red-300'
                              }`}
                            >
                              {scope.scope_type}
                            </span>
                            <code className="text-gray-300">
                              {scope.value}
                            </code>
                          </div>
                          <button
                            onClick={() =>
                              handleDeleteScope(target.id, scope.id)
                            }
                            className="p-1 hover:bg-red-900/20 rounded text-gray-400 hover:text-red-400 transition"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Botón de eliminar */}
                  <button
                    onClick={() => handleDeleteTarget(target.id)}
                    className="w-full mt-4 px-4 py-2 bg-red-900/20 hover:bg-red-900/40 text-red-400 border border-red-700 rounded transition flex items-center justify-center gap-2"
                  >
                    <Trash2 size={18} />
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
