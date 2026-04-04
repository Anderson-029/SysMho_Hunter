import React from 'react';
import { motion } from 'framer-motion';

/**
 * Sidebar - Organismo de navegación lateral con Glassmorphism.
 */
const Sidebar = ({ activeView, onViewChange }) => {
  const navItems = [
    { id: 'dashboard', icon: '⚡', label: 'Dashboard' },
    { id: 'scanner', icon: '🎯', label: 'Inyección & Scan' },
    { id: 'findings', icon: '🐛', label: 'Hallazgos' },
    { id: 'reports', icon: '📄', label: 'Reportes' },
    { id: 'settings', icon: '⚙️', label: 'Opciones' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar__logo">
        <motion.div 
          whileHover={{ rotate: 180 }}
          className="sidebar__logo-icon"
        >
          SH
        </motion.div>
        <div>
          <div className="sidebar__logo-text gradient-text">SysMho Hunter</div>
          <div className="sidebar__logo-version">Core v1.0.0 — Secured</div>
        </div>
      </div>
      
      <nav className="sidebar__nav">
        {navItems.map(item => (
          <motion.button
            key={item.id}
            whileHover={{ x: 5 }}
            whileTap={{ scale: 0.95 }}
            className={`sidebar__nav-item ${activeView === item.id ? 'sidebar__nav-item--active' : ''}`}
            onClick={() => onViewChange(item.id)}
          >
            <span className="sidebar__nav-icon">{item.icon}</span>
            <span className="sidebar__nav-label">{item.label}</span>
          </motion.button>
        ))}
      </nav>
      
      <div className="sidebar__footer" style={{ padding: '24px', opacity: 0.4, fontSize: '0.65rem' }}>
        © 2026 SysMho Hunter AI System
      </div>
    </aside>
  );
};

export default Sidebar;
