import { useState } from 'react'
import { Upload, X, CheckCircle, AlertCircle } from 'lucide-react'

interface ScopeImporterProps {
  targetId: string
  onClose: () => void
  onSuccess: () => void
  isLoading?: boolean
}

export function ScopeImporter({
  targetId,
  onClose,
  onSuccess,
  isLoading = false,
}: ScopeImporterProps) {
  const [scopeType, setScopeType] = useState('domain')
  const [isInScope, setIsInScope] = useState(true)
  const [values, setValues] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>(
    'idle'
  )
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')

    const scopeLines = values
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)

    if (scopeLines.length === 0) {
      setStatus('error')
      setMessage('Ingresa al menos un scope')
      return
    }

    try {
      const { api } = await import('../api/client')
      const data = await api.post(`/targets/${targetId}/scopes/bulk`, {
        values: scopeLines,
        scope_type: scopeType,
        is_in_scope: isInScope,
      })

      setStatus('success')
      setMessage(`✅ ${data.length} scopes importados exitosamente`)
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1500)
    } catch (err) {
      setStatus('error')
      setMessage(`Error: ${err instanceof Error ? err.message : 'Desconocido'}`)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-lg w-full">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">Importar Scopes</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Tipo de scope */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tipo de Scope
            </label>
            <select
              value={scopeType}
              onChange={e => setScopeType(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
            >
              <option value="domain">Dominio</option>
              <option value="url">URL</option>
              <option value="ip">IP</option>
              <option value="cidr">CIDR</option>
              <option value="wildcard">Wildcard</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {scopeType === 'domain' && 'ej: example.com, api.example.com'}
              {scopeType === 'url' && 'ej: https://example.com/api'}
              {scopeType === 'ip' && 'ej: 192.168.1.1, 10.0.0.5'}
              {scopeType === 'cidr' && 'ej: 192.168.1.0/24, 10.0.0.0/8'}
              {scopeType === 'wildcard' && 'ej: *.example.com'}
            </p>
          </div>

          {/* Estado in/out of scope */}
          <div className="flex items-center gap-3 p-3 bg-gray-800 border border-gray-700 rounded">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isInScope}
                onChange={e => setIsInScope(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm text-gray-300">
                {isInScope ? '✅ In Scope' : '❌ Out of Scope'}
              </span>
            </label>
          </div>

          {/* Área de entrada */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Ingresa los valores (uno por línea)
            </label>
            <textarea
              value={values}
              onChange={e => setValues(e.target.value)}
              rows={8}
              placeholder={
                scopeType === 'domain'
                  ? 'api.example.com\nweb.example.com\nadmin.example.com'
                  : scopeType === 'url'
                    ? 'https://api.example.com/v1\nhttps://web.example.com'
                    : scopeType === 'ip'
                      ? '192.168.1.1\n10.0.0.5'
                      : scopeType === 'cidr'
                        ? '192.168.1.0/24\n10.0.0.0/8'
                        : '*.example.com\n*.api.example.com'
              }
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none font-mono text-sm"
              disabled={isLoading}
            />
          </div>

          {/* Estado */}
          {status !== 'idle' && (
            <div
              className={`p-3 rounded flex items-center gap-2 ${
                status === 'success'
                  ? 'bg-green-900/30 border border-green-700 text-green-300'
                  : status === 'error'
                    ? 'bg-red-900/30 border border-red-700 text-red-300'
                    : 'bg-blue-900/30 border border-blue-700 text-blue-300'
              }`}
            >
              {status === 'success' && <CheckCircle size={18} />}
              {status === 'error' && <AlertCircle size={18} />}
              <span className="text-sm">{message}</span>
            </div>
          )}

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
              disabled={isLoading || status === 'success'}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-2 transition disabled:opacity-50"
            >
              <Upload size={18} />
              {isLoading ? 'Importando...' : 'Importar Scopes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
