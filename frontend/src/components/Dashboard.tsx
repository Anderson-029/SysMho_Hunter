import { useEffect, useState, useRef } from 'react'
import { motion, useMotionValue, animate } from 'framer-motion'
import {
  Activity,
  Target,
  Bug,
  Clock,
  Zap,
  Wifi,
  WifiOff,
  LogOut,
  Terminal,
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useScanStore } from '../stores/scanStore'
import { ScanMonitor } from './ScanMonitor'
import { FindingsList } from './FindingsList'
import { PendingActions } from './PendingActions'
import { LiveLogs } from './LiveLogs'
import { TargetsManager } from './TargetsManager'
import { CommandApprovalModal } from './CommandApprovalModal'
import { TerminalPanel } from './TerminalPanel'

/* ------------------------------------------------------------------ */
/* Componente de número animado                                         */
/* ------------------------------------------------------------------ */
function AnimatedNumber({ value }: { value: number }) {
  const motionVal = useMotionValue(0)
  const [display, setDisplay] = useState(0)
  const prevRef = useRef(0)

  useEffect(() => {
    const controls = animate(motionVal, value, {
      duration: 0.7,
      ease: 'easeOut',
    })
    const unsub = motionVal.on('change', v => setDisplay(Math.round(v)))
    prevRef.current = value
    return () => {
      controls.stop()
      unsub()
    }
  }, [value]) // eslint-disable-line

  return <>{display}</>
}

/* ------------------------------------------------------------------ */
/* Tipos de tabs                                                        */
/* ------------------------------------------------------------------ */
type TabId = 'targets' | 'scans' | 'findings' | 'actions' | 'logs' | 'terminal'

const SEV_COLOR: Record<string, string> = {
  critical: '#ff3366',
  high: '#f97316',
  medium: '#ffd700',
  low: '#00bfff',
  informational: '#6b7280',
}

/* ------------------------------------------------------------------ */
/* Dashboard principal                                                  */
/* ------------------------------------------------------------------ */
export function Dashboard() {
  const { user, logout } = useAuthStore()
  const {
    targets,
    scans,
    findings,
    pendingActions,
    fetchTargets,
    fetchScans,
    fetchFindings,
    fetchPendingActions,
    connectWebSocket,
    wsConnected,
  } = useScanStore()

  const [activeTab, setActiveTab] = useState<TabId>('targets')

  const handleLogout = async () => {
    await logout()
    // AuthGuard se encargará de re-renderizar al cambiar isAuthenticated
  }

  useEffect(() => {
    fetchTargets()
    fetchScans()
    fetchFindings()
    fetchPendingActions()
    connectWebSocket()
  }, []) // eslint-disable-line

  /* Métricas */
  const activeScans = scans.filter(s => s.status === 'running').length
  const criticalCount = findings.filter(f => f.severity === 'critical').length
  const highCount = findings.filter(f => f.severity === 'high').length

  /* Datos para el donut chart */
  const severityData = [
    { name: 'CRITICAL', value: criticalCount, color: '#ff3366' },
    { name: 'HIGH', value: highCount, color: '#f97316' },
    {
      name: 'MEDIUM',
      value: findings.filter(f => f.severity === 'medium').length,
      color: '#ffd700',
    },
    {
      name: 'LOW',
      value: findings.filter(f => f.severity === 'low').length,
      color: '#00bfff',
    },
  ].filter(d => d.value > 0)

  /* Stats cards */
  const stats = [
    {
      label: 'TARGETS',
      value: targets.length,
      color: '#00bfff',
      Icon: Target,
    },
    {
      label: 'SCANS ACTIVOS',
      value: activeScans,
      color: '#00ff88',
      Icon: Activity,
    },
    {
      label: 'CRÍTICOS',
      value: criticalCount,
      color: '#ff3366',
      Icon: Bug,
    },
    {
      label: 'FINDINGS ALTOS',
      value: highCount,
      color: '#f97316',
      Icon: Zap,
    },
  ]

  /* Tabs */
  const TABS: { id: TabId; label: string; Icon: React.ElementType; badge?: number }[] = [
    { id: 'targets', label: 'PROGRAMAS', Icon: Target },
    { id: 'scans', label: 'SCANS', Icon: Activity },
    { id: 'findings', label: 'FINDINGS', Icon: Bug, badge: findings.length },
    { id: 'actions', label: 'ACCIONES', Icon: Zap, badge: pendingActions.length },
    { id: 'logs', label: 'LOGS', Icon: Clock },
    { id: 'terminal', label: 'TERMINAL', Icon: Terminal },
  ]

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0a0e1a' }}>
      {/* ── HEADER ── */}
      <div
        className="border-b sticky top-0 z-10"
        style={{ borderColor: '#1f2937', backgroundColor: '#111827' }}
      >
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span style={{ color: '#00ff88', fontSize: '18px' }}>◈</span>
            <h1
              className="text-base font-bold tracking-widest"
              style={{ color: '#00ff88' }}
            >
              SYSMHO HUNTER
            </h1>
            <span
              className="text-xs px-2 py-0.5 rounded"
              style={{ backgroundColor: '#1f2937', color: '#4b5563' }}
            >
              v0.2.0
            </span>
          </div>
          <div className="flex items-center gap-4">
            {/* WS Status */}
            <div className="flex items-center gap-1.5 text-xs">
              {wsConnected ? (
                <Wifi size={13} style={{ color: '#00ff88' }} />
              ) : (
                <WifiOff size={13} style={{ color: '#ff3366' }} />
              )}
              <span style={{ color: wsConnected ? '#00ff88' : '#ff3366' }}>
                {wsConnected ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>

            {/* User + Logout */}
            {user && (
              <div className="flex items-center gap-3 pl-4 border-l" style={{ borderColor: '#1f2937' }}>
                <span className="text-xs" style={{ color: '#9ca3af' }}>
                  {user.username}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-opacity-80 transition"
                  style={{
                    backgroundColor: 'rgba(255, 51, 102, 0.1)',
                    color: '#ff3366',
                  }}
                  title="Logout"
                >
                  <LogOut size={14} />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── STATS + CHART ── */}
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex gap-4">
          {/* Cards */}
          <div className="grid grid-cols-2 gap-3 flex-1">
            {stats.map(stat => (
              <motion.div
                key={stat.label}
                className="rounded border p-4 flex items-start justify-between"
                style={{
                  backgroundColor: '#111827',
                  borderColor: '#1f2937',
                }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div>
                  <div
                    className="text-xs mb-1.5"
                    style={{ color: '#4b5563', letterSpacing: '0.5px' }}
                  >
                    {stat.label}
                  </div>
                  <div
                    className="text-3xl font-bold"
                    style={{ color: stat.color }}
                  >
                    <AnimatedNumber value={stat.value} />
                  </div>
                </div>
                <stat.Icon
                  size={18}
                  style={{ color: stat.color, opacity: 0.4, marginTop: 2 }}
                />
              </motion.div>
            ))}
          </div>

          {/* Donut chart de severidad */}
          {severityData.length > 0 && (
            <div
              className="rounded border flex flex-col items-center justify-center"
              style={{
                backgroundColor: '#111827',
                borderColor: '#1f2937',
                width: '200px',
                flexShrink: 0,
                padding: '16px 8px',
              }}
            >
              <div
                className="text-xs mb-2"
                style={{ color: '#4b5563', letterSpacing: '0.5px' }}
              >
                FINDINGS POR SEV.
              </div>
              <ResponsiveContainer width="100%" height={120}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={32}
                    outerRadius={50}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {severityData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      border: '1px solid #1f2937',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontFamily: 'inherit',
                    }}
                    formatter={(v, name) => [v, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col gap-1 w-full px-2 mt-1">
                {severityData.map(d => (
                  <div
                    key={d.name}
                    className="flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-1">
                      <span
                        className="inline-block w-2 h-2 rounded-sm"
                        style={{ backgroundColor: SEV_COLOR[d.name.toLowerCase()] || d.color }}
                      />
                      <span style={{ color: '#6b7280' }}>
                        {d.name.slice(0, 4)}
                      </span>
                    </div>
                    <span style={{ color: d.color }}>{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── TABS ── */}
      <div className="max-w-7xl mx-auto px-6">
        <div
          className="flex gap-0.5 border-b"
          style={{ borderColor: '#1f2937' }}
        >
          {TABS.map(tab => {
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="flex items-center gap-1.5 px-4 py-3 text-xs font-bold tracking-widest transition-colors relative"
                style={{
                  color: isActive ? '#00ff88' : '#4b5563',
                  fontFamily: 'inherit',
                  background: 'none',
                  border: 'none',
                  borderBottom: isActive
                    ? '2px solid #00ff88'
                    : '2px solid transparent',
                  cursor: 'pointer',
                  paddingBottom: '11px',
                }}
              >
                <tab.Icon size={13} />
                {tab.label}
                {tab.badge != null && tab.badge > 0 && (
                  <span
                    className="text-xs px-1.5 py-0.5 rounded-full font-bold"
                    style={{
                      backgroundColor:
                        tab.id === 'actions' ? '#ff3366' : '#1f2937',
                      color: tab.id === 'actions' ? '#fff' : '#9ca3af',
                      fontSize: '10px',
                    }}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Contenido del tab activo */}
        <motion.div
          key={activeTab}
          className="py-4"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'targets' && <TargetsManager />}
          {activeTab === 'scans' && <ScanMonitor />}
          {activeTab === 'findings' && <FindingsList />}
          {activeTab === 'actions' && <PendingActions />}
          {activeTab === 'logs' && <LiveLogs />}
          {activeTab === 'terminal' && <TerminalPanel />}
        </motion.div>
      </div>

      {/* Modal de aprobación — siempre montado, aparece con AnimatePresence */}
      <CommandApprovalModal />
    </div>
  )
}
