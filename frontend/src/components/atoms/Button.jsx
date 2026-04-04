import React from 'react';
import { motion } from 'framer-motion';

/**
 * Button - Componente Atomo Premium.
 * Soporta variantes, tamaños y estados de carga.
 */
const Button = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'md', 
  isLoading = false, 
  disabled = false,
  fullWidth = false,
  icon: Icon,
  className = '',
  type = 'button'
}) => {
  const baseClass = 'btn';
  const variantClass = `btn--${variant}`;
  const sizeClass = size !== 'md' ? `btn--${size}` : '';
  const fullWidthStyle = fullWidth ? { width: '100%' } : {};

  return (
    <motion.button
      type={type}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${baseClass} ${variantClass} ${sizeClass} ${className}`}
      style={fullWidthStyle}
      onClick={onClick}
      disabled={disabled || isLoading}
    >
      {isLoading ? (
        <span className="spinner"></span>
      ) : (
        <>
          {Icon && <Icon size={18} />}
          {children}
        </>
      )}
    </motion.button>
  );
};

export default Button;
