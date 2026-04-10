#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Stop script seguro y completo
# Detiene todos los procesos en orden inverso
# Limpia recursos, evita procesos zombies
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS_DIR="$ROOT/.pids"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_ok() { echo -e "${GREEN}✅${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠️${NC}  $1"; }
log_info() { echo -e "${BLUE}▶${NC} $1"; }

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║     SysMho Hunter — Deteniendo todos los servicios║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# Función para matar procesos de forma segura
# ============================================================
kill_process() {
    local name="$1"
    local pidfile="$2"
    local pattern="$3"  # Patrón alternativo si el PID file no existe

    local pid=""

    # Intenta leer del archivo .pid
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile" 2>/dev/null || true)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            # PID válido, intenta kill suave primero
            log_info "Deteniendo $name (PID: $pid)..."
            if kill -TERM "$pid" 2>/dev/null; then
                # Espera a que termine gracefully
                local count=0
                while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                    sleep 0.5
                    ((count++))
                done
                # Si aún está vivo, force kill
                if kill -0 "$pid" 2>/dev/null; then
                    log_warn "  $name no respondió a TERM. Usando KILL..."
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
            log_ok "$name detenido"
            rm -f "$pidfile"
        else
            rm -f "$pidfile" 2>/dev/null || true
        fi
    fi

    # Fallback: buscar por patrón si el pid file no existía o falló
    if [ -n "$pattern" ]; then
        local count
        count=$(pgrep -f "$pattern" 2>/dev/null | wc -l || echo "0")
        if [ "$count" -gt 0 ]; then
            log_info "Finalizando instancias remanentes de $name..."
            pkill -f "$pattern" 2>/dev/null || true
            sleep 1
            # Force kill si persisten
            if pgrep -f "$pattern" &>/dev/null; then
                pkill -9 -f "$pattern" 2>/dev/null || true
            fi
            log_ok "$name (remanentes) limpiado"
        fi
    fi
}

# ============================================================
# 1. Frontend (Vite)
# ============================================================
log_info "Deteniendo Frontend..."
kill_process "Frontend" "$PIDS_DIR/frontend.pid" "vite"

echo ""

# ============================================================
# 2. Backend (uvicorn)
# ============================================================
log_info "Deteniendo Backend..."
kill_process "Backend" "$PIDS_DIR/backend.pid" "uvicorn app.main"

echo ""

# ============================================================
# 3. Ollama
# ============================================================
log_info "Deteniendo Ollama..."
kill_process "Ollama" "$PIDS_DIR/ollama.pid" "ollama serve"

echo ""

# ============================================================
# 4. Limpieza de procesos zombies
# ============================================================
log_info "Limpiando procesos zombies..."

# Matar cualquier instancia remanente de npm
pkill -f "npm run dev" 2>/dev/null || true

# Matar node (vite es un proceso node)
pkill -f "vite" 2>/dev/null || true

# Matar uvicorn directo
pkill -f "uvicorn" 2>/dev/null || true

sleep 1

# Verificar que no queden procesos
local_port_procs() {
    local port="$1"
    local name="$2"
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warn "$name aún escucha en puerto $port. Matando..."
        fuser -k $port/tcp 2>/dev/null || true
    fi
}

local_port_procs 8000 "Backend"
local_port_procs 5173 "Frontend"
local_port_procs 11434 "Ollama"

echo ""

# ============================================================
# 5. Limpiar archivos PID
# ============================================================
rm -rf "$PIDS_DIR" 2>/dev/null || true
log_ok "Archivos PID limpiados"

echo ""

# ============================================================
# 6. Resumen final
# ============================================================
echo "╔════════════════════════════════════════════════════╗"
echo "║           ✅ Detención completada                 ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Estado de puertos:"
echo "   8000 (Backend):  $(lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 && echo '❌ ABIERTO' || echo '✅ Libre')"
echo "   5173 (Frontend): $(lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 && echo '❌ ABIERTO' || echo '✅ Libre')"
echo "   11434 (Ollama):  $(lsof -Pi :11434 -sTCP:LISTEN -t >/dev/null 2>&1 && echo '❌ ABIERTO' || echo '✅ Libre')"
echo ""
echo "Para iniciar de nuevo:"
echo "   bash $ROOT/scripts/start_hunter.sh"
echo ""
