import React from 'react';
import { motion } from 'framer-motion';

/**
 * Topbar - Organismo superior para estado y navegación.
 */
const Topbar = ({ title, isConnected }) => {
  return (
    <header className="topbar">
      <div className="topbar__content">
        <motion.span 
          initial={{ opacity: 0, x: -10 }} 
          animate={{ opacity: 1, x: 0 }}
          className="topbar__title"
        >
          {title}
        </motion.span>
      </div>
      
      <div className="topbar__status">
        <motion.div 
          animate={{ scale: isConnected ? [1, 1.2, 1] : 1 }}
          transition={{ repeat: Infinity, duration: 2 }}
          className={`topbar__status-dot ${!isConnected ? 'topbar__status-dot--offline' : ''}`}
        />
        <span className="gradient-text" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
          {isConnected ? 'AGENTE ONLINE' : 'OFFLINE'}
        </span>
      </div>
    </header>
  );
};

export default Topbar;
