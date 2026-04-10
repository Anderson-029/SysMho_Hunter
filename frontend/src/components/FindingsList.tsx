import { useState, useMemo } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  BrainCircuit,
} from 'lucide-react'
import { useScanStore } from '../stores/scanStore'
import type { Finding } from '../types'

const SEV_COLOR: Record<string, string> = {
  critical: '#ff3366',
  high: '#f97316',
  medium: '#ffd700',
  low: '#00bfff',
  informational: '#6b7280',
}

const SEV_ORDER = ['critical', 'high', 'medium', 'low', 'informational']

export function FindingsList() {
  const { findings } = useScanStore()
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'severity', desc: false },
  ])
  const [globalFilter, setGlobalFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filteredFindings = useMemo(() => {
    if (severityFilter === 'all') return findings
    return findings.filter(f => f.severity === severityFilter)
  }, [findings, severityFilter])

  const columns = useMemo<ColumnDef<Finding>[]>(
    () => [
      {
        id: 'severity',
        accessorFn: row =>
          SEV_ORDER.indexOf(row.severity || 'informational'),
        header: 'SEV',
        cell: ({ row }) => {
          const sev = row.original.severity || 'informational'
          const color = SEV_COLOR[sev]
          return (
            <span
              className="text-xs font-bold px-1.5 py-0.5 rounded"
              style={{ color, border: `1px solid ${color}` }}
            >
              {sev.slice(0, 4).toUpperCase()}
            </span>
          )
        },
        size: 72,
      },
      {
        accessorKey: 'title',
        header: 'TÍTULO',
        cell: ({ getValue }) => (
          <span className="text-xs" style={{ color: '#e5e7eb' }}>
            {getValue<string>()}
          </span>
        ),
      },
      {
        accessorKey: 'vuln_type',
        header: 'TIPO',
        cell: ({ getValue }) => (
          <span className="text-xs font-mono" style={{ color: '#00bfff' }}>
            {getValue<string>() || '—'}
          </span>
        ),
        size: 110,
      },
      {
        accessorKey: 'cvss_score',
        header: 'CVSS',
        cell: ({ getValue }) => {
          const v = getValue<number | undefined>()
          return (
            <span style={{ color: '#ffd700', fontSize: '11px' }}>
              {v != null ? v.toFixed(1) : '—'}
            </span>
          )
        },
        size: 62,
      },
      {
        id: 'ml_confidence',
        accessorFn: row => row.ml_confidence,
        header: 'ML',
        cell: ({ row }) => {
          const conf = row.original.ml_confidence
          return conf != null ? (
            <span style={{ color: '#9333ea', fontSize: '11px' }}>
              {(conf * 100).toFixed(0)}%
            </span>
          ) : (
            <span style={{ color: '#374151', fontSize: '11px' }}>—</span>
          )
        },
        size: 52,
      },
      {
        accessorKey: 'url',
        header: 'URL',
        cell: ({ getValue }) => (
          <span
            className="text-xs font-mono"
            style={{
              color: '#6b7280',
              display: 'block',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '200px',
            }}
          >
            {getValue<string>() || '—'}
          </span>
        ),
      },
      {
        accessorKey: 'discovered_at',
        header: 'FECHA',
        cell: ({ getValue }) => (
          <span style={{ color: '#4b5563', fontSize: '11px' }}>
            {getValue<string>()?.slice(0, 10) || '—'}
          </span>
        ),
        size: 90,
      },
    ],
    [],
  )

  const table = useReactTable({
    data: filteredFindings,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 20 } },
  })

  const SortIcon = ({ colId }: { colId: string }) => {
    const col = table.getColumn(colId)
    if (!col) return <ChevronsUpDown size={10} style={{ opacity: 0.3 }} />
    const sorted = col.getIsSorted()
    if (sorted === 'asc') return <ChevronUp size={10} />
    if (sorted === 'desc') return <ChevronDown size={10} />
    return <ChevronsUpDown size={10} style={{ opacity: 0.3 }} />
  }

  if (findings.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center py-12 gap-2"
        style={{ color: '#4b5563' }}
      >
        <BrainCircuit size={28} style={{ color: '#00ff8840' }} />
        <span className="text-xs">
          No hay findings. Inicia un scan para descubrir vulnerabilidades.
        </span>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Barra de filtros */}
      <div className="flex items-center gap-2 flex-wrap">
        <div
          className="flex items-center gap-1.5 flex-1 min-w-0 rounded px-2 py-1.5"
          style={{ backgroundColor: '#111827', border: '1px solid #1f2937' }}
        >
          <Search size={12} style={{ color: '#4b5563', flexShrink: 0 }} />
          <input
            value={globalFilter}
            onChange={e => setGlobalFilter(e.target.value)}
            placeholder="Buscar título, URL, tipo..."
            className="bg-transparent text-xs outline-none w-full"
            style={{ color: '#e5e7eb', fontFamily: 'inherit' }}
          />
        </div>
        <div
          className="flex items-center gap-1.5 rounded px-2 py-1.5"
          style={{ backgroundColor: '#111827', border: '1px solid #1f2937' }}
        >
          <Filter size={12} style={{ color: '#4b5563' }} />
          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="bg-transparent text-xs outline-none"
            style={{ color: '#e5e7eb', fontFamily: 'inherit' }}
          >
            <option value="all">Todos</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="informational">Info</option>
          </select>
        </div>
        <span className="text-xs" style={{ color: '#4b5563' }}>
          {table.getFilteredRowModel().rows.length} findings
        </span>
      </div>

      {/* Tabla */}
      <div
        className="rounded border overflow-auto"
        style={{ borderColor: '#1f2937' }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(header => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{
                      padding: '8px 10px',
                      textAlign: 'left',
                      cursor: header.column.getCanSort() ? 'pointer' : 'default',
                      backgroundColor: '#0a0e1a',
                      color: '#6b7280',
                      fontWeight: 700,
                      letterSpacing: '0.5px',
                      borderBottom: '1px solid #1f2937',
                      userSelect: 'none',
                      width: header.getSize() !== 150 ? header.getSize() : undefined,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    <span className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      <SortIcon colId={header.id} />
                    </span>
                  </th>
                ))}
                {/* Columna de expansión */}
                <th
                  style={{
                    padding: '8px 10px',
                    backgroundColor: '#0a0e1a',
                    borderBottom: '1px solid #1f2937',
                    width: 32,
                  }}
                />
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map(row => {
              const isExpanded = expandedId === row.original.id
              return (
                <>
                  <tr
                    key={row.id}
                    style={{
                      borderBottom: '1px solid #1f293740',
                      backgroundColor: isExpanded ? '#111827' : 'transparent',
                      cursor: 'pointer',
                    }}
                    onClick={() =>
                      setExpandedId(isExpanded ? null : row.original.id)
                    }
                  >
                    {row.getVisibleCells().map(cell => (
                      <td
                        key={cell.id}
                        style={{ padding: '7px 10px', verticalAlign: 'middle' }}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                    <td style={{ padding: '7px 10px', textAlign: 'center' }}>
                      {row.original.brain_reasoning && (
                        <BrainCircuit size={12} style={{ color: '#9333ea', opacity: 0.7 }} />
                      )}
                    </td>
                  </tr>
                  {isExpanded && row.original.brain_reasoning && (
                    <tr key={`${row.id}-detail`}>
                      <td
                        colSpan={columns.length + 1}
                        style={{ padding: '0 10px 10px' }}
                      >
                        <div
                          className="text-xs rounded p-2"
                          style={{ backgroundColor: '#0a0e1a', color: '#9ca3af' }}
                        >
                          🧠 {row.original.brain_reasoning}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {table.getPageCount() > 1 && (
        <div className="flex items-center justify-between text-xs" style={{ color: '#6b7280' }}>
          <span>
            Página {table.getState().pagination.pageIndex + 1} de{' '}
            {table.getPageCount()}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="p-1 rounded"
              style={{ color: table.getCanPreviousPage() ? '#e5e7eb' : '#374151' }}
            >
              <ChevronLeft size={14} />
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="p-1 rounded"
              style={{ color: table.getCanNextPage() ? '#e5e7eb' : '#374151' }}
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
