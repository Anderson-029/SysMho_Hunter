import React from 'react';

/**
 * Badge - Componente Atomo para etiquetas de severidad y estados.
 */
const Badge = ({ 
  children, 
  severity = 'info', 
  className = '',
  dot = true
}) => {
  const baseClass = 'severity-pill';
  const severityClass = `severity-pill--${severity}`;

  return (
    <span className={`${baseClass} ${severityClass} ${className}`}>
      {dot && <span className="severity-dot" />}
      {children}
    </span>
  );
};

export default Badge;
