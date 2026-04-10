#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Datos iniciales en agent_config
# ============================================================

set -euo pipefail

# Leer .env si existe
if [ -f "backend/.env" ]; then
    export $(grep -v '^#' backend/.env | xargs)
fi

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-sysmho_hunter}"

echo "Insertando configuración inicial en agent_config..."

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'SQL'
INSERT INTO agent_config (key, value, description) VALUES
    ('brain.ml_confidence_threshold',    '{"value": 0.85}', 'Umbral de confianza para usar respuesta ML directamente'),
    ('brain.local_llm_confidence_threshold', '{"value": 0.70}', 'Umbral de confianza para Ollama antes de delegar a cloud'),
    ('brain.active_brain',               '{"value": "auto"}', 'auto|ml|local|cloud — cerebro a usar. auto = cadena de fallback'),
    ('brain.ollama_model',               '{"value": "llama3.1:8b-instruct-q6_K"}', 'Modelo Ollama para nivel 2'),
    ('recon.max_concurrent_tools',       '{"value": 5}', 'Herramientas ejecutándose en paralelo por fase'),
    ('recon.default_timeout',            '{"value": 300}', 'Timeout por defecto para herramientas CLI (segundos)'),
    ('recon.default_phases',             '{"value": ["subdomain_enum", "port_scan", "web_fingerprint", "crawl", "vuln_scan"]}', 'Fases de reconocimiento por defecto'),
    ('scope.strict_mode',                '{"value": true}', 'Si true, rechaza cualquier target fuera de scope sin excepción'),
    ('actions.auto_approve_low_risk',    '{"value": false}', 'Si true, aprueba automáticamente pending_actions con risk_level=low'),
    ('report.h1_min_quality_score',      '{"value": 7}', 'Score mínimo (0-10) para considerar un reporte listo para H1')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
SQL

echo "✅ Seed completado."
