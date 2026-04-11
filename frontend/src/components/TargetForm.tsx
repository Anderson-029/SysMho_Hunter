import { useState } from 'react'
import type { Target } from '../types'
import { Save, X, AlertTriangle } from 'lucide-react'

interface TargetFormProps {
  onSubmit: (target: Partial<Target>) => Promise<void>
  onClose: () => void
  isLoading?: boolean
}

export function TargetForm({
  onSubmit,
  onClose,
  isLoading = false,
}: TargetFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    organization: '',
    platform: 'hackerone',
    program_url: '',
    priority: 5,
    safe_harbor: true,
    rules_md: '',
    out_of_scope_notes: '',
    bounty_table: {} as Record<string, string>,
  })

  const [bountyLevels, setBountyLevels] = useState([
    { level: 'low', amount: '' },
    { level: 'medium', amount: '' },
    { level: 'high', amount: '' },
    { level: 'critical', amount: '' },
  ])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const bounty_table = bountyLevels.reduce(
      (acc, { level, amount }) => {
        if (amount) acc[level] = amount
        return acc
      },
      {} as Record<string, string>
    )

    await onSubmit({
      ...formData,
      bounty_table,
    })
  }

  const handleBountyChange = (level: string, amount: string) => {
    setBountyLevels(lvls =>
      lvls.map(l => (l.level === level ? { ...l, amount } : l))
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">Crear Programa Manual</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Datos básicos */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-200">
              Información Básica
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Nombre del Programa *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={e =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                  placeholder="ej: Acme Corp H1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Organización
                </label>
                <input
                  type="text"
                  value={formData.organization}
                  onChange={e =>
                    setFormData({ ...formData, organization: e.target.value })
                  }
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                  placeholder="ej: Acme Corp"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Plataforma *
                </label>
                <select
                  value={formData.platform}
                  onChange={e =>
                    setFormData({ ...formData, platform: e.target.value })
                  }
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                >
                  <option value="hackerone">HackerOne</option>
                  <option value="bugcrowd">Bugcrowd</option>
                  <option value="intigriti">Intigriti</option>
                  <option value="yeswehack">YesWeHack</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Prioridad (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.priority}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      priority: parseInt(e.target.value),
                    })
                  }
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                URL del Programa
              </label>
              <input
                type="url"
                value={formData.program_url}
                onChange={e =>
                  setFormData({ ...formData, program_url: e.target.value })
                }
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                placeholder="https://hackerone.com/..."
              />
            </div>
          </div>

          {/* Safe Harbor */}
          <div className="flex items-center gap-2 p-3 bg-gray-800 border border-gray-700 rounded">
            <input
              type="checkbox"
              id="safe_harbor"
              checked={formData.safe_harbor}
              onChange={e =>
                setFormData({ ...formData, safe_harbor: e.target.checked })
              }
              className="w-4 h-4"
            />
            <label htmlFor="safe_harbor" className="text-sm text-gray-300">
              El programa tiene Safe Harbor
            </label>
            {!formData.safe_harbor && (
              <div className="flex items-center gap-1 text-yellow-500 text-sm ml-auto">
                <AlertTriangle size={16} />
                <span>⚠️ Sin protección legal</span>
              </div>
            )}
          </div>

          {/* Reglas */}
          <div>
            <h3 className="text-lg font-semibold text-gray-200 mb-2">
              Reglas del Programa
            </h3>
            <label className="block text-sm text-gray-400 mb-2">
              Pega las reglas en markdown del programa (permitido, prohibido, etc)
            </label>
            <textarea
              value={formData.rules_md}
              onChange={e =>
                setFormData({ ...formData, rules_md: e.target.value })
              }
              rows={6}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none font-mono text-sm"
              placeholder="## Políticas de Seguridad&#10;&#10;### Está Permitido:&#10;- Testing en dominios en scope&#10;- SQL Injection testing&#10;&#10;### Prohibido:&#10;- Denial of Service&#10;- Social engineering"
            />
          </div>

          {/* Out of scope */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notas Out of Scope
            </label>
            <textarea
              value={formData.out_of_scope_notes}
              onChange={e =>
                setFormData({
                  ...formData,
                  out_of_scope_notes: e.target.value,
                })
              }
              rows={3}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
              placeholder="ej: No testear: Backups, Staging, Employee systems"
            />
          </div>

          {/* Bounty Table */}
          <div>
            <h3 className="text-lg font-semibold text-gray-200 mb-3">
              Tabla de Recompensas
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {bountyLevels.map(({ level }) => (
                <div key={level}>
                  <label className="block text-sm text-gray-400 mb-1 capitalize">
                    {level}
                  </label>
                  <input
                    type="text"
                    value={bountyLevels.find(l => l.level === level)?.amount || ''}
                    onChange={e =>
                      handleBountyChange(level, e.target.value)
                    }
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                    placeholder="ej: $100"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-300 border border-gray-700 rounded hover:bg-gray-800 transition"
              disabled={isLoading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-2 transition disabled:opacity-50"
            >
              <Save size={18} />
              {isLoading ? 'Guardando...' : 'Crear Programa'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
