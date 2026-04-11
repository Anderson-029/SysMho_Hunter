#!/bin/bash

################################################################################
# SysMho Hunter — Script de ARRANQUE
# Inicia el sistema completo en orden lógico con verificaciones
# Uso: bash scripts/start_sysmho.sh
################################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/.pids/sysmho.pids"

# Crear directorio de logs y pids
mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$PID_FILE")"

# Archivo de log
LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"

################################################################################
# FUNCIONES HELPER
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 no está instalado"
        return 1
    fi
    return 0
}

check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Puerto está en uso
    fi
    return 1  # Puerto está libre
}

wait_for_port() {
    local port=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    log_info "Esperando que $name esté disponible en puerto $port..."

    while ! check_port "$port"; do
        if [ $attempt -eq $max_attempts ]; then
            log_error "$name no respondió en puerto $port después de $max_attempts intentos"
            return 1
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo ""
    log_success "$name está disponible en puerto $port"
    return 0
}

cleanup_on_exit() {
    log_warning "Interrupción detectada. Limpiando procesos..."
    # Los procesos hijos se limpiarán en el script stop
}

trap cleanup_on_exit SIGINT SIGTERM

################################################################################
# 1. VERIFICACIONES INICIALES
################################################################################

log_info "═══════════════════════════════════════════════════════════════"
log_info "SysMho Hunter — Iniciando sistema"
log_info "═══════════════════════════════════════════════════════════════"

log_info "Directorio base: $PROJECT_ROOT"
log_info "Log de esta sesión: $LOG_FILE"

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_ROOT/CLAUDE.md" ]; then
    log_error "No se encontró CLAUDE.md. ¿Estás en el directorio correcto?"
    exit 1
fi

# Verificar dependencias instaladas
log_info "Verificando dependencias..."
check_command "python3" || exit 1
check_command "psql" || exit 1
check_command "ollama" || exit 1
check_command "npm" || exit 1
check_command "uv" || exit 1
log_success "Todas las dependencias están instaladas"

# Verificar puertos disponibles
log_info "Verificando puertos disponibles..."
for port in 5432 11434 8000 5173; do
    if check_port "$port"; then
        log_warning "Puerto $port ya está en uso. Se intentará usar el proceso existente."
    else
        log_success "Puerto $port disponible"
    fi
done

################################################################################
# 2. POSTGRESQL
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "1/5 POSTGRESQL"
log_info "───────────────────────────────────────────────────────────────"

# Verificar si está corriendo
if check_port 5432; then
    log_success "PostgreSQL ya está corriendo en puerto 5432"
else
    log_info "Iniciando PostgreSQL..."
    sudo systemctl start postgresql >> "$LOG_FILE" 2>&1
    sleep 2

    if ! wait_for_port 5432 "PostgreSQL"; then
        log_error "No se pudo iniciar PostgreSQL"
        exit 1
    fi
fi

# Verificar conexión
log_info "Verificando conexión a BD..."
if PGPASSWORD="ander123" psql -h 127.0.0.1 -U postgres -d sysmho_hunter -c "SELECT 1" >> "$LOG_FILE" 2>&1; then
    log_success "Conexión a BD verificada"
else
    log_error "No se pudo conectar a la BD"
    exit 1
fi

################################################################################
# 3. OLLAMA
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "2/5 OLLAMA (LLM Local)"
log_info "───────────────────────────────────────────────────────────────"

# Verificar si está corriendo
if check_port 11434; then
    log_success "Ollama ya está corriendo en puerto 11434"
else
    log_info "Iniciando Ollama..."
    ollama serve >> "$LOG_DIR/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    echo "$OLLAMA_PID" >> "$PID_FILE"

    if ! wait_for_port 11434 "Ollama"; then
        log_error "No se pudo iniciar Ollama"
        exit 1
    fi
fi

# Verificar modelo
log_info "Verificando modelo llama3.1..."
if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "llama3.1:8b-instruct-q6_k"; then
    log_success "Modelo llama3.1:8b-instruct-q6_k disponible"
else
    log_warning "Modelo no encontrado. Descargando..."
    log_info "Esto puede tomar 10-15 minutos la primera vez..."
    ollama pull llama3.1:8b-instruct-q6_k >> "$LOG_DIR/ollama.log" 2>&1
    log_success "Modelo descargado"
fi

################################################################################
# 4. BACKEND
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "3/5 BACKEND (FastAPI)"
log_info "───────────────────────────────────────────────────────────────"

cd "$BACKEND_DIR"

# Instalar dependencias
log_info "Verificando dependencias de backend..."
if [ ! -d ".venv" ]; then
    log_info "Ejecutando uv sync..."
    uv sync >> "$LOG_FILE" 2>&1
    log_success "Dependencias instaladas"
else
    log_success "Dependencias ya instaladas"
fi

# Migraciones
log_info "Aplicando migraciones de BD..."
if uv run alembic upgrade head >> "$LOG_FILE" 2>&1; then
    log_success "Migraciones aplicadas"
else
    log_error "Error al aplicar migraciones"
    exit 1
fi

# Verificar .env
if [ ! -f ".env" ]; then
    log_error ".env no encontrado en backend/"
    exit 1
fi
log_success ".env presente"

# Arrancar backend
log_info "Iniciando uvicorn en puerto 8000..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >> "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >> "$PID_FILE"

if ! wait_for_port 8000 "Backend"; then
    log_error "No se pudo iniciar Backend"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Verificar health
log_info "Verificando health del backend..."
sleep 2
if curl -s http://localhost:8000/health | grep -q '"status":"online"'; then
    log_success "Backend está online y funcional"
else
    log_error "Backend no respondió correctamente"
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

# Instalar dependencias
if [ ! -d "node_modules" ]; then
    log_info "Ejecutando npm install..."
    npm install >> "$LOG_FILE" 2>&1
    log_success "Dependencias instaladas"
else
    log_success "Dependencias ya instaladas"
fi

# Arrancar frontend
log_info "Iniciando Vite dev server en puerto 5173..."
npm run dev >> "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PID_FILE"

if ! wait_for_port 5173 "Frontend"; then
    log_error "No se pudo iniciar Frontend"
    kill $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

################################################################################
# 6. VERIFICACIÓN FINAL
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "5/5 VERIFICACIÓN FINAL"
log_info "───────────────────────────────────────────────────────────────"

sleep 2

# Todos los checks
log_info "Verificando componentes..."

# PostgreSQL
if PGPASSWORD="ander123" psql -h 127.0.0.1 -U postgres -d sysmho_hunter -c "SELECT 1" >> /dev/null 2>&1; then
    log_success "PostgreSQL ✓"
else
    log_error "PostgreSQL ✗"
fi

# Ollama
if curl -s http://localhost:11434/api/tags >> /dev/null 2>&1; then
    log_success "Ollama ✓"
else
    log_error "Ollama ✗"
fi

# Backend
if curl -s http://localhost:8000/health | grep -q "online" >> /dev/null 2>&1; then
    log_success "Backend API ✓"
else
    log_error "Backend API ✗"
fi

# Frontend
if curl -s http://localhost:5173 | grep -q "html" >> /dev/null 2>&1; then
    log_success "Frontend UI ✓"
else
    log_error "Frontend UI ✗"
fi

################################################################################
# RESUMEN FINAL
################################################################################

log_info ""
log_info "═══════════════════════════════════════════════════════════════"
log_success "SysMho Hunter iniciado correctamente ✓"
log_info "═══════════════════════════════════════════════════════════════"

echo ""
echo -e "${GREEN}📱 DASHBOARD:${NC}          http://localhost:5173"
echo -e "${GREEN}🔧 BACKEND API:${NC}       http://localhost:8000"
echo -e "${GREEN}📊 API DOCS:${NC}          http://localhost:8000/docs"
echo -e "${GREEN}🤖 OLLAMA:${NC}            http://localhost:11434"
echo -e "${GREEN}🗄️  POSTGRESQL:${NC}       localhost:5432"
echo ""
echo -e "${YELLOW}PIDs guardados en:${NC}    $PID_FILE"
echo -e "${YELLOW}Log de esta sesión:${NC}   $LOG_FILE"
echo ""
echo -e "${YELLOW}Para apagar:${NC}          bash scripts/stop_sysmho.sh"
echo ""

log_success "Sistema listo para trabajar"
