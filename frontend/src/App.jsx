import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Hooks
import { useWebSocket } from './hooks/useWebSocket';
import { useScanner } from './hooks/useScanner';

// Atoms
import Button from './components/atoms/Button';
import StatCard from './components/molecules/StatCard';

// Organisms
import Sidebar from './components/organisms/Sidebar';
import Topbar from './components/organisms/Topbar';
import Terminal from './components/organisms/Terminal';
import FindingsTable from './components/organisms/FindingsTable';

// Molecules
import ScanProgress from './components/molecules/ScanProgress';

// Lucide Icons (se cargan bajo demanda si estuvieran disponibles, de lo contrario usaremos placeholders visuales)
const BugIcon = () => <span>🐛</span>;
const ShieldIcon = () => <span>🛡️</span>;
const AlertIcon = () => <span>🔴</span>;
const HighIcon = () => <span>🟠</span>;

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [targetUrl, setTargetUrl] = useState('');
  
  const { messages, isConnected } = useWebSocket('ws://127.0.0.1:8000/ws/live');
  const { 
    isScanning, 
    scanStatus, 
    findings, 
    logs, 
    startScan,
    setLogs 
  } = useScanner();

  // Integrar logs en tiempo real del WebSocket al estado local de logs
  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.type === 'log') {
        setLogs(prev => [...prev, lastMsg.data]);
      }
    }
  }, [messages, setLogs]);

  const handleStart = async () => {
    if (!targetUrl.trim()) return;
    await startScan(targetUrl);
  };

  const severityCounts = findings.reduce((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="app-layout">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      
      <Topbar 
        title={activeView.toUpperCase()} 
        isConnected={isConnected} 
      />

      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeView}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.25 }}
          >
            {activeView === 'dashboard' && (
              <div className="view-container">
                {/* Dashboard Stats */}
                <div className="stats-grid">
                  <StatCard label="Hallazgos Totales" value={findings.length} icon={BugIcon} color="#4f46e5" />
                  <StatCard label="Críticos Detectados" value={severityCounts.critical || 0} icon={AlertIcon} color="#ef4444" />
                  <StatCard label="Puntos Altos" value={severityCounts.high || 0} icon={HighIcon} color="#f97316" />
                  <StatCard label="Estatus Agente" value={isConnected ? "READY" : "OFFLINE"} icon={ShieldIcon} color="#22c55e" />
                </div>

                {/* Scanner Interface */}
                <div className="card glass-panel shadow-lg" style={{ marginBottom: '28px' }}>
                  <div className="card__header">
                    <span className="card__title gradient-text">🎯 Nuevo Objetivo de Pentesting</span>
                    {isScanning && <div className="spinner" />}
                  </div>
                  
                  <div className="input-group">
                    <input
                      type="text"
                      className="input"
                      placeholder="https://target-pentest.com"
                      value={targetUrl}
                      onChange={(e) => setTargetUrl(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleStart()}
                      disabled={isScanning}
                    />
                    <Button 
                      onClick={handleStart} 
                      isLoading={isScanning}
                      disabled={!targetUrl.trim()}
                    >
                      LANZAR ATAQUE
                    </Button>
                  </div>

                  {scanStatus && (
                    <ScanProgress status={scanStatus.status} />
                  )}
                </div>

                {/* Dual View: Terminal & Findings */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                   <Terminal logs={logs} />
                   <FindingsTable findings={findings} />
                </div>
              </div>
            )}

            {activeView !== 'dashboard' && (
              <div className="card glass-panel" style={{ padding: '60px', textAlign: 'center' }}>
                <h2 className="gradient-text">Sección {activeView} en construcción...</h2>
                <p style={{ opacity: 0.6 }}>Estamos migrando esta vista a la nueva arquitectura atómica.</p>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
