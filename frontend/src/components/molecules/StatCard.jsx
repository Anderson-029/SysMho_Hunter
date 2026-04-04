import React from 'react';
import { motion } from 'framer-motion';

/**
 * StatCard - Molecule para el Dashboard.
 * Muestra una métrica con icono decorativo y gradientes premium.
 */
const StatCard = ({ label, value, icon: Icon, color = '#4f46e5' }) => {
  return (
    <motion.div 
      whileHover={{ y: -5 }}
      className="stat-card" 
      style={{ '--stat-color': color }}
    >
      <div className="stat-card__header">
        <span className="stat-card__label">{label}</span>
        {Icon && (
          <div className="stat-card__icon" style={{ color: color }}>
            <Icon size={20} />
          </div>
        )}
      </div>
      <div className="stat-card__content">
        <span className="stat-card__value">{value}</span>
      </div>
      {/* Efecto de brillo de fondo */}
      <div 
        className="stat-card__glow" 
        style={{ background: `radial-gradient(circle at 50% 50%, ${color}1a, transparent 70%)` }}
      />
    </motion.div>
  );
};

export default StatCard;
