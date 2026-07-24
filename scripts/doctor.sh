#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Doctor: diagnóstico de bases
# Uso: bash scripts/doctor.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PASS=0
FAIL=0
WARN=0

ok() { echo -e "${GREEN}[OK]${NC} $1"; PASS=$((PASS + 1)); }
bad() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARN=$((WARN + 1)); }

# Cargar backend/.env (sin heredar DB_* de la shell)
unset DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME LOCAL_LLM_BASE_URL \
    LOCAL_LLM_API_KEY QDRANT_URL
if [ -f "backend/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source backend/.env
    set +a
    ok "backend/.env presente"
else
    bad "backend/.env no encontrado (copia backend/.env.example)"
fi

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_NAME="${DB_NAME:-sysmho_hunter}"
LOCAL_LLM_BASE_URL="${LOCAL_LLM_BASE_URL:-http://localhost:1234/v1}"
LOCAL_LLM_API_KEY="${LOCAL_LLM_API_KEY:-}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"

echo ""
echo "=== Docker Compose ==="
if command -v docker >/dev/null 2>&1; then
    ok "docker instalado"
    if docker compose ps --status running 2>/dev/null | grep -q sysmho_postgres; then
        ok "sysmho_postgres running"
    else
        warn "sysmho_postgres no running (docker compose up -d)"
    fi
    if docker compose ps --status running 2>/dev/null | grep -q sysmho_qdrant; then
        ok "sysmho_qdrant running"
    else
        warn "sysmho_qdrant no running (docker compose up -d)"
    fi
else
    bad "docker no instalado"
fi

echo ""
echo "=== PostgreSQL ==="
if [ -n "$DB_PASSWORD" ] && PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
    ok "Postgres $DB_HOST:$DB_PORT/$DB_NAME"
else
    bad "No se puede conectar a Postgres ($DB_HOST:$DB_PORT/$DB_NAME)"
fi

echo ""
echo "=== Qdrant ==="
if curl -sf "${QDRANT_URL}/readyz" >/dev/null 2>&1; then
    ok "Qdrant ready (${QDRANT_URL})"
else
    bad "Qdrant no responde en ${QDRANT_URL}/readyz"
fi

echo ""
echo "=== Local LLM (OpenAI-compatible) ==="
LLM_URL="${LOCAL_LLM_BASE_URL%/}/models"
AUTH_HDR=()
if [ -n "$LOCAL_LLM_API_KEY" ]; then
    AUTH_HDR=(-H "Authorization: Bearer ${LOCAL_LLM_API_KEY}")
fi
if curl -sf --max-time 3 "${AUTH_HDR[@]}" "$LLM_URL" >/dev/null 2>&1; then
    ok "Local LLM responde en $LLM_URL"
else
    warn "Local LLM no responde en $LLM_URL (LM Studio Local Server / Ollama /v1)"
fi

echo ""
echo "=== Backend / Frontend ==="
if curl -sf --max-time 3 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    HEALTH=$(curl -sf --max-time 3 http://127.0.0.1:8000/health)
    ok "Backend health: $HEALTH"
else
    warn "Backend no responde en :8000"
fi

if curl -sf --max-time 3 http://localhost:5173/ >/dev/null 2>&1; then
    ok "Frontend en :5173"
else
    warn "Frontend no responde en :5173"
fi

echo ""
echo "=== ML models ==="
if [ -f "ml/models/severity_classifier.pkl" ]; then
    ok "Modelos ML presentes"
else
    warn "Modelos ML .pkl ausentes (Nivel 1 unavailable — esperado si no se entrenaron)"
fi

echo ""
echo "=== Resumen ==="
echo "OK=$PASS  WARN=$WARN  FAIL=$FAIL"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
