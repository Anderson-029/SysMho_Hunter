#!/bin/bash

################################################################################
# SysMho Hunter — Script de ARRANQUE
# Inicia el sistema completo en orden lógico con verificaciones
# Uso: bash scripts/start_sysmho.sh
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/.pids/sysmho.pids"

mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$PID_FILE")"
: > "$PID_FILE"

LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"

log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"; }

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 no está instalado"
        return 1
    fi
    return 0
}

check_port() {
    local port=$1
    if command -v nc &> /dev/null; then
        nc -z localhost "$port" >/dev/null 2>&1 && return 0
    fi
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

wait_for_port() {
    local port=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    log_info "Esperando que $name esté disponible en puerto $port..."
    while ! check_port "$port"; do
        if [ "$attempt" -eq "$max_attempts" ]; then
            log_error "$name no respondió en puerto $port"
            return 1
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo ""
    log_success "$name está disponible en puerto $port"
    return 0
}

load_backend_env() {
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        log_error "backend/.env no encontrado. Copia backend/.env.example"
        exit 1
    fi
    set -a
    # shellcheck disable=SC1091
    source "$BACKEND_DIR/.env"
    set +a
    DB_HOST="${DB_HOST:-127.0.0.1}"
    DB_PORT="${DB_PORT:-5432}"
    DB_USER="${DB_USER:-postgres}"
    DB_PASSWORD="${DB_PASSWORD:-}"
    DB_NAME="${DB_NAME:-sysmho_hunter}"
    LOCAL_LLM_BASE_URL="${LOCAL_LLM_BASE_URL:-http://localhost:1234/v1}"
    LOCAL_LLM_API_KEY="${LOCAL_LLM_API_KEY:-}"
    QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
    if [ -z "$DB_PASSWORD" ]; then
        log_error "DB_PASSWORD vacía en backend/.env"
        exit 1
    fi
}

################################################################################
# 1. VERIFICACIONES
################################################################################

log_info "═══════════════════════════════════════════════════════════════"
log_info "SysMho Hunter — Iniciando sistema"
log_info "═══════════════════════════════════════════════════════════════"
log_info "Directorio base: $PROJECT_ROOT"

if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
    log_error "No se encontró CLAUDE.md"
    exit 1
fi

load_backend_env
log_success "backend/.env cargado"

log_info "Verificando dependencias..."
check_command "python3" || exit 1
check_command "docker" || exit 1
check_command "npm" || exit 1
check_command "uv" || exit 1
check_command "curl" || exit 1
log_success "Dependencias CLI OK"

################################################################################
# 2. DOCKER INFRA (Postgres + Qdrant)
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "1/5 DOCKER INFRA (Postgres + Qdrant)"
log_info "───────────────────────────────────────────────────────────────"

cd "$PROJECT_ROOT"
# Alinear .env raíz para compose (DB_* desde backend/.env)
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    cat > "$PROJECT_ROOT/.env" << EOF
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
EOF
fi

log_info "Levantando docker compose..."
if ! docker compose up -d >> "$LOG_FILE" 2>&1; then
    log_error "docker compose up -d falló"
    log_error "Si el puerto $DB_PORT está ocupado por otro Postgres, detenlo primero."
    exit 1
fi

log_info "Esperando health de Postgres..."
for i in $(seq 1 30); do
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >> "$LOG_FILE" 2>&1; then
        log_success "PostgreSQL conectado ($DB_HOST:$DB_PORT/$DB_NAME)"
        break
    fi
    if [ "$i" -eq 30 ]; then
        log_error "PostgreSQL no respondió. ¿Puerto $DB_PORT libre? Ver logs de compose."
        exit 1
    fi
    sleep 1
done

log_info "Esperando Qdrant..."
for i in $(seq 1 30); do
    if curl -sf "${QDRANT_URL}/readyz" >/dev/null 2>&1; then
        log_success "Qdrant ready ($QDRANT_URL)"
        break
    fi
    if [ "$i" -eq 30 ]; then
        log_error "Qdrant no respondió en $QDRANT_URL"
        exit 1
    fi
    sleep 1
done

################################################################################
# 3. LOCAL LLM (OpenAI-compatible)
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "2/5 LOCAL LLM (OpenAI-compatible)"
log_info "───────────────────────────────────────────────────────────────"

LLM_MODELS_URL="${LOCAL_LLM_BASE_URL%/}/models"
AUTH_ARGS=()
if [ -n "$LOCAL_LLM_API_KEY" ]; then
    AUTH_ARGS=(-H "Authorization: Bearer ${LOCAL_LLM_API_KEY}")
fi

if curl -sf "${AUTH_ARGS[@]}" "$LLM_MODELS_URL" >/dev/null 2>&1; then
    log_success "Local LLM disponible ($LLM_MODELS_URL)"
else
    log_warning "Local LLM no responde en $LLM_MODELS_URL"
    log_warning "Activa LM Studio Local Server (u otro OpenAI-compat)."
    log_warning "El cerebro usará Nivel 3 (cloud) si Gemini está configurado."
fi

################################################################################
# 4. BACKEND
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "3/5 BACKEND (FastAPI)"
log_info "───────────────────────────────────────────────────────────────"

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    log_info "Ejecutando uv sync..."
    uv sync >> "$LOG_FILE" 2>&1
    log_success "Dependencias instaladas"
else
    log_success "Dependencias ya instaladas"
fi

log_info "Aplicando migraciones..."
if uv run alembic upgrade head >> "$LOG_FILE" 2>&1; then
    log_success "Migraciones aplicadas"
else
    log_error "Error al aplicar migraciones"
    exit 1
fi

log_info "Iniciando uvicorn en puerto 8000..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >> "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >> "$PID_FILE"

if ! wait_for_port 8000 "Backend"; then
    log_error "No se pudo iniciar Backend"
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

sleep 2
if curl -s http://localhost:8000/health | grep -q '"status":"online"'; then
    log_success "Backend online"
else
    log_error "Backend no respondió /health"
    exit 1
fi

################################################################################
# 5. FRONTEND
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "4/5 FRONTEND (React + Vite)"
log_info "───────────────────────────────────────────────────────────────"

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    log_info "Ejecutando npm install..."
    npm install >> "$LOG_FILE" 2>&1
    log_success "Dependencias instaladas"
else
    log_success "Dependencias ya instaladas"
fi

log_info "Iniciando Vite en puerto 5173..."
npm run dev >> "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PID_FILE"

if ! wait_for_port 5173 "Frontend"; then
    log_error "No se pudo iniciar Frontend"
    kill "$FRONTEND_PID" 2>/dev/null || true
    exit 1
fi

################################################################################
# 6. VERIFICACIÓN FINAL
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "5/5 VERIFICACIÓN FINAL"
log_info "───────────────────────────────────────────────────────────────"

if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
    log_success "PostgreSQL ✓"
else
    log_error "PostgreSQL ✗"
fi

if curl -sf "${QDRANT_URL}/readyz" >/dev/null 2>&1; then
    log_success "Qdrant ✓"
else
    log_error "Qdrant ✗"
fi

if curl -sf "${AUTH_ARGS[@]}" "$LLM_MODELS_URL" >/dev/null 2>&1; then
    log_success "Local LLM ✓"
else
    log_warning "Local LLM ✗ (opcional si usas solo cloud)"
fi

if curl -s http://localhost:8000/health | grep -q "online"; then
    log_success "Backend API ✓"
else
    log_error "Backend API ✗"
fi

if curl -s http://localhost:5173 | grep -qi "html"; then
    log_success "Frontend UI ✓"
else
    log_error "Frontend UI ✗"
fi

log_info ""
log_info "═══════════════════════════════════════════════════════════════"
log_success "SysMho Hunter iniciado"
log_info "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Dashboard:${NC}     http://localhost:5173"
echo -e "${GREEN}Backend API:${NC}    http://localhost:8000"
echo -e "${GREEN}API Docs:${NC}       http://localhost:8000/docs"
echo -e "${GREEN}Local LLM:${NC}      $LOCAL_LLM_BASE_URL"
echo -e "${GREEN}Qdrant:${NC}         $QDRANT_URL"
echo -e "${GREEN}PostgreSQL:${NC}     $DB_HOST:$DB_PORT"
echo ""
echo -e "${YELLOW}Doctor:${NC}         bash scripts/doctor.sh"
echo -e "${YELLOW}Parar:${NC}          bash scripts/stop_sysmho.sh"
echo ""
