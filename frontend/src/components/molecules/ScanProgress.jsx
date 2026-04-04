import React from 'react';
import { motion } from 'framer-motion';

/**
 * ScanProgress - Molecule que visualiza las fases del Pentesting.
 */
const ScanProgress = ({ status }) => {
  const steps = [
    { id: 'recon', label: 'Recon' },
    { id: 'analyzing', label: 'Analysis' },
    { id: 'reporting', label: 'Report' },
    { id: 'completed', label: 'Done' }
  ];
  
  const currentIndex = steps.findIndex(s => s.id === status);

  return (
    <div className="scan-progress-container card glass-panel" style={{ padding: '20px', marginTop: '12px' }}>
      <div className="scan-progress">
        {steps.map((step, i) => (
          <div key={step.id} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <motion.div
              initial={false}
              animate={{ 
                background: i <= currentIndex ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                boxShadow: i === currentIndex ? '0 0 15px var(--accent-primary-glow)' : 'none'
              }}
              className={`scan-progress__step ${i === currentIndex ? 'scan-progress__step--active' : ''}`}
            />
            <span style={{ 
              fontSize: '0.65rem', 
              textAlign: 'center', 
              color: i <= currentIndex ? 'var(--text-primary)' : 'var(--text-muted)',
              fontWeight: i === currentIndex ? 700 : 400
            }}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScanProgress;
