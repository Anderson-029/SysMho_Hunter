import React from 'react';
import Badge from '../atoms/Badge';

/**
 * FindingsTable - Organismo para mostrar vulnerabilidades detectadas.
 * Estructura tabular premium con badges semánticos.
 */
const FindingsTable = ({ findings = [] }) => {
  if (!findings.length) {
    return (
      <div className="card glass-panel shadow-md" style={{ textAlign: 'center', padding: '60px 24px' }}>
        <span style={{ fontSize: '3rem', marginBottom: '16px', display: 'block' }}>🛸</span>
        <p className="gradient-text" style={{ fontWeight: 500 }}>
          No se han detectado anomalías en el objetivo aún.
        </p>
      </div>
    );
  }

  return (
    <div className="card glass-panel shadow-lg" style={{ padding: 0, overflow: 'hidden' }}>
      <table className="findings-table">
        <thead>
          <tr>
            <th>Severidad</th>
            <th>Vulnerabilidad</th>
            <th>Tipo</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((finding, i) => (
            <tr key={i}>
              <td>
                <Badge severity={finding.severity}>
                  {finding.severity}
                </Badge>
              </td>
              <td style={{ fontWeight: 600 }}>{finding.title}</td>
              <td style={{ opacity: 0.8 }}>{finding.type}</td>
              <td>
                <Badge severity="success" dot={false}>NUEVO</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default FindingsTable;
