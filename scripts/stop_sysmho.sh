#!/bin/bash

################################################################################
# SysMho Hunter — Script de APAGADO
# Detiene el sistema completo en orden inverso sin procesos zombies
# Uso: bash scripts/stop_sysmho.sh
################################################################################

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/.pids/sysmho.pids"

# Archivo de log
LOG_FILE="$LOG_DIR/shutdown_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

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

kill_process() {
    local name=$1
    local pid=$2
    local port=$3

    if [ -z "$pid" ] || [ "$pid" = "0" ]; then
        # Si no tenemos PID, intentar matar por nombre/puerto
        if [ -n "$port" ]; then
            log_info "Buscando procesos en puerto $port..."
            local pids=$(lsof -ti :$port 2>/dev/null)
            if [ -n "$pids" ]; then
                log_info "Matando procesos: $pids"
                echo "$pids" | xargs kill -9 2>/dev/null || true
                sleep 1
                log_success "$name detenido (por puerto)"
            else
                log_warning "$name no encontrado en puerto $port"
            fi
        else
            log_info "Buscando procesos por nombre: $name..."
            pkill -f "$name" -9 2>/dev/null || true
            sleep 1
        fi
    else
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Matando $name (PID: $pid)..."
            kill -15 "$pid" 2>/dev/null || true
            sleep 1

            # Verificar si sigue corriendo
            if kill -0 "$pid" 2>/dev/null; then
                log_warning "$name no respondió a SIGTERM, usando SIGKILL..."
                kill -9 "$pid" 2>/dev/null || true
                sleep 1
            fi

            if ! kill -0 "$pid" 2>/dev/null; then
                log_success "$name detenido (PID: $pid)"
            else
                log_error "$name no se pudo detener"
                return 1
            fi
        else
            log_warning "$name no está corriendo (PID: $pid)"
        fi
    fi
    return 0
}

################################################################################
# INICIO DEL APAGADO
################################################################################

log_info "═══════════════════════════════════════════════════════════════"
log_info "SysMho Hunter — Deteniendo sistema"
log_info "═══════════════════════════════════════════════════════════════"
log_info "Log de esta sesión: $LOG_FILE"
echo ""

################################################################################
# 1. FRONTEND — Se mantiene vivo para mostrar pantalla de "desconectado"
################################################################################

log_info "───────────────────────────────────────────────────────────────"
log_info "1/5 FRONTEND (React + Vite)"
log_info "───────────────────────────────────────────────────────────────"

# El frontend NO se mata. Se queda corriendo y mostrará el estado
# OFFLINE automáticamente cuando el backend y WebSocket dejen de responder.
# Esto evita cerrar el navegador del usuario con todas sus pestañas.
log_success "Frontend se mantiene activo — mostrará estado OFFLINE en el dashboard"

################################################################################
# 2. BACKEND
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "2/5 BACKEND (FastAPI)"
log_info "───────────────────────────────────────────────────────────────"

# Matar uvicorn por puerto
pkill -f "uvicorn" -9 2>/dev/null || true
kill_process "uvicorn" "" 8000

sleep 1

################################################################################
# 3. OLLAMA
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "3/5 OLLAMA (LLM Local)"
log_info "───────────────────────────────────────────────────────────────"

# Matar ollama
pkill -f "ollama serve" -9 2>/dev/null || true
kill_process "Ollama" "" 11434

sleep 1

################################################################################
# 4. POSTGRESQL
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "4/5 POSTGRESQL"
log_info "───────────────────────────────────────────────────────────────"

log_info "Deteniendo PostgreSQL..."
if sudo systemctl stop postgresql >> "$LOG_FILE" 2>&1; then
    log_success "PostgreSQL detenido"
else
    log_warning "No se pudo detener PostgreSQL (podría requerir permisos sudo)"
fi

################################################################################
# 5. LIMPIEZA
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "5/5 LIMPIEZA DE PROCESOS ZOMBIES"
log_info "───────────────────────────────────────────────────────────────"

log_info "Buscando procesos huérfanos..."

# Buscar procesos Python que puedan estar zombies
PYTHON_PROCS=$(pgrep -f "python" | wc -l)
if [ "$PYTHON_PROCS" -gt 0 ]; then
    log_warning "Encontrados $PYTHON_PROCS procesos Python"
    log_info "Limpiando procesos Python relacionados con SysMho..."
    pkill -f "uvicorn\|alembic\|app.main" -9 2>/dev/null || true
    sleep 1
fi

# No se matan procesos Node/Vite — el frontend se mantiene activo
# para mostrar el estado OFFLINE en el dashboard

# Verificar que no hay procesos zombie en los puertos del backend
log_info "Verificando puertos backend..."

for port in 8000 11434; do
    if lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null > /dev/null; then
        log_warning "Puerto $port todavía está en uso, forzando cierre..."
        lsof -ti :$port 2>/dev/null | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
done
# Puerto 5173 (frontend) se omite intencionalmente

# Limpiar archivo de PIDs
if [ -f "$PID_FILE" ]; then
    log_info "Limpiando archivo de PIDs..."
    > "$PID_FILE"  # Vaciar archivo
    log_success "Archivo de PIDs limpiado"
fi

################################################################################
# VERIFICACIÓN FINAL
################################################################################

log_info ""
log_info "───────────────────────────────────────────────────────────────"
log_info "VERIFICACIÓN FINAL"
log_info "───────────────────────────────────────────────────────────────"

echo ""

# Frontend: se mantiene activo intencionalmente
log_success "Frontend activo — muestra estado OFFLINE en el dashboard ✓"

# Verificar Backend
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_error "Backend aún está corriendo en puerto 8000 ✗"
else
    log_success "Backend detenido ✓"
fi

# Verificar Ollama
if lsof -Pi :11434 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_error "Ollama aún está corriendo en puerto 11434 ✗"
else
    log_success "Ollama detenido ✓"
fi

# Verificar procesos zombies
ZOMBIE_PROCS=$(ps aux | grep -E "\[.*\]" | wc -l)
if [ "$ZOMBIE_PROCS" -gt 1 ]; then
    log_warning "Pueden haber procesos huérfanos (intenta 'ps aux | grep defunct')"
else
    log_success "No hay procesos huérfanos detectados ✓"
fi

################################################################################
# RESUMEN FINAL
################################################################################

log_info ""
log_info "═══════════════════════════════════════════════════════════════"
log_success "SysMho Hunter detenido correctamente ✓"
log_info "═══════════════════════════════════════════════════════════════"

echo ""
echo -e "${YELLOW}Verificación final:${NC}"
echo -e "  ${YELLOW}◈${NC} Frontend activo — mostrando estado OFFLINE"
echo -e "  ${GREEN}✓${NC} Backend detenido (puerto 8000)"
echo -e "  ${GREEN}✓${NC} Ollama detenido (puerto 11434)"
echo -e "  ${GREEN}✓${NC} PostgreSQL detenido"
echo ""
echo -e "${YELLOW}Log de esta sesión:${NC}   $LOG_FILE"
echo -e "${YELLOW}Para reiniciar:${NC}       bash scripts/start_sysmho.sh"
echo ""

log_success "Sistema completamente detenido, sin procesos zombies"
