import React, { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Terminal - Organismo de visualización de logs.
 * Diseño estilo hacker premium con scroll automático y animaciones.
 */
const Terminal = ({ logs = [] }) => {
  const bodyRef = useRef(null);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogClass = (level) => {
    const levels = {
      success: 'terminal__text--success',
      error: 'terminal__text--error',
      warning: 'terminal__text--warning',
      info: 'terminal__text--info',
    };
    return levels[level] || '';
  };

  return (
    <div className="terminal glass-panel shadow-lg">
      <div className="terminal__header">
        <div className="terminal__dot terminal__dot--red" />
        <div className="terminal__dot terminal__dot--yellow" />
        <div className="terminal__dot terminal__dot--green" />
        <span className="terminal__title">SysMho Hunter — Agent Consola</span>
      </div>
      
      <div className="terminal__body" ref={bodyRef}>
        <AnimatePresence initial={false}>
          {logs.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }}
              className="terminal__line"
            >
              <span className="terminal__prefix">$</span>
              <span className="terminal__text animate-pulse-slow">
                A la espera de objetivos de Pentesting...
              </span>
            </motion.div>
          ) : (
            logs.map((log, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.1 }}
                className="terminal__line"
              >
                <span className="terminal__timestamp">
                  [{new Date(log.timestamp || log.created_at).toLocaleTimeString()}]
                </span>
                <span className="terminal__prefix">›</span>
                <span className={`terminal__text ${getLogClass(log.level)}`}>
                  {log.message}
                </span>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Terminal;
