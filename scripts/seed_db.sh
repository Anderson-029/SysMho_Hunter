#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Datos iniciales en agent_config
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Leer backend/.env
if [ -f "backend/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source backend/.env
    set +a
fi

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-sysmho_hunter}"
LOCAL_LLM_MODEL="${LOCAL_LLM_MODEL:-local-model}"

if [ -z "$DB_PASSWORD" ]; then
    echo "ERROR: DB_PASSWORD no definida. Configura backend/.env"
    exit 1
fi

echo "Insertando configuración inicial en agent_config..."

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << SQL
INSERT INTO agent_config (key, value, description) VALUES
    ('brain.ml_confidence_threshold',    '{"value": 0.85}', 'Umbral de confianza para usar respuesta ML directamente'),
    ('brain.local_llm_confidence_threshold', '{"value": 0.70}', 'Umbral de confianza para Local LLM antes de delegar a cloud'),
    ('brain.active_brain',               '{"value": "auto"}', 'auto|ml|local|cloud — cerebro a usar. auto = cadena de fallback'),
    ('brain.local_llm_model',            '{"value": "${LOCAL_LLM_MODEL}"}', 'Modelo local (OpenAI-compatible) para nivel 2'),
    ('recon.max_concurrent_tools',       '{"value": 5}', 'Herramientas ejecutándose en paralelo por fase'),
    ('recon.default_timeout',            '{"value": 300}', 'Timeout por defecto para herramientas CLI (segundos)'),
    ('recon.default_phases',             '{"value": ["subdomain_enum", "port_scan", "web_fingerprint", "crawl", "vuln_scan"]}', 'Fases de reconocimiento por defecto'),
    ('scope.strict_mode',                '{"value": true}', 'Si true, rechaza cualquier target fuera de scope sin excepción'),
    ('actions.auto_approve_low_risk',    '{"value": false}', 'Si true, aprueba automáticamente pending_actions con risk_level=low'),
    ('report.h1_min_quality_score',      '{"value": 7}', 'Score mínimo (0-10) para considerar un reporte listo para H1')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
SQL

echo "✅ Seed completado."
