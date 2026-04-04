#!/usr/bin/env bash
# ============================================================
# SysMho Hunter - Script de Detención
# Detiene todos los servicios en orden lógico:
# 1. Cerrar Frontend (Vite)
# 2. Cerrar Backend (FastAPI/Uvicorn)
# 3. Limpiar archivos PID
# (PostgreSQL se deja corriendo porque puede ser usado
# por otros servicios del sistema)
# ============================================================

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Directorio base del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE_DIR="${PROJECT_DIR}/.pids"
BACKEND_PID_FILE="${PIDFILE_DIR}/backend.pid"
FRONTEND_PID_FILE="${PIDFILE_DIR}/frontend.pid"

# Banner
echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║       🛑 SysMho Hunter - Deteniendo...      ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ─────────────────────────────────────────────
# Paso 1: Detener Frontend
# ─────────────────────────────────────────────
echo -e "${YELLOW}[1/3]${NC} Deteniendo Frontend..."

if [ -f "${FRONTEND_PID_FILE}" ]; then
    FRONTEND_PID=$(cat "${FRONTEND_PID_FILE}")
    if kill -0 "${FRONTEND_PID}" 2>/dev/null; then
        # Matar el proceso y todos sus hijos (node/vite)
        kill -- -"${FRONTEND_PID}" 2>/dev/null || kill "${FRONTEND_PID}" 2>/dev/null
        sleep 1
        # Forzar si sigue vivo
        if kill -0 "${FRONTEND_PID}" 2>/dev/null; then
            kill -9 "${FRONTEND_PID}" 2>/dev/null
        fi
        echo -e "${GREEN}  ✔ Frontend detenido (PID ${FRONTEND_PID})${NC}"
    else
        echo -e "${YELLOW}  ⚠ Frontend ya no estaba corriendo${NC}"
    fi
    rm -f "${FRONTEND_PID_FILE}"
else
    echo -e "${YELLOW}  ⚠ No se encontró PID del frontend${NC}"
fi

# Matar cualquier proceso vite huérfano en el puerto 5173
VITE_PID=$(lsof -ti:5173 2>/dev/null || true)
if [ -n "${VITE_PID}" ]; then
    kill ${VITE_PID} 2>/dev/null || true
    echo -e "${GREEN}  ✔ Proceso huérfano en puerto 5173 eliminado${NC}"
fi

# ─────────────────────────────────────────────
# Paso 2: Detener Backend
# ─────────────────────────────────────────────
echo -e "${YELLOW}[2/3]${NC} Deteniendo Backend..."

if [ -f "${BACKEND_PID_FILE}" ]; then
    BACKEND_PID=$(cat "${BACKEND_PID_FILE}")
    if kill -0 "${BACKEND_PID}" 2>/dev/null; then
        # Enviar SIGTERM primero (cierre graceful)
        kill "${BACKEND_PID}" 2>/dev/null
        sleep 2
        # Forzar si sigue vivo
        if kill -0 "${BACKEND_PID}" 2>/dev/null; then
            kill -9 "${BACKEND_PID}" 2>/dev/null
        fi
        echo -e "${GREEN}  ✔ Backend detenido (PID ${BACKEND_PID})${NC}"
    else
        echo -e "${YELLOW}  ⚠ Backend ya no estaba corriendo${NC}"
    fi
    rm -f "${BACKEND_PID_FILE}"
else
    echo -e "${YELLOW}  ⚠ No se encontró PID del backend${NC}"
fi

# Matar cualquier proceso uvicorn huérfano en el puerto 8000
UVICORN_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "${UVICORN_PID}" ]; then
    kill ${UVICORN_PID} 2>/dev/null || true
    sleep 1
    # Verificar y forzar
    UVICORN_PID=$(lsof -ti:8000 2>/dev/null || true)
    if [ -n "${UVICORN_PID}" ]; then
        kill -9 ${UVICORN_PID} 2>/dev/null || true
    fi
    echo -e "${GREEN}  ✔ Procesos huérfanos en puerto 8000 eliminados${NC}"
fi

# ─────────────────────────────────────────────
# Paso 3: Limpieza
# ─────────────────────────────────────────────
echo -e "${YELLOW}[3/3]${NC} Limpiando archivos temporales..."

# Limpiar directorio de PIDs
rm -rf "${PIDFILE_DIR}"
echo -e "${GREEN}  ✔ Archivos PID eliminados${NC}"

# Nota: NO detenemos PostgreSQL porque puede ser
# usado por otras aplicaciones del sistema.
echo -e "${YELLOW}  ℹ PostgreSQL se deja corriendo (uso compartido)${NC}"

# ─────────────────────────────────────────────
# Resumen
# ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}  ╔══════════════════════════════════════════════╗"
echo -e "  ║     ${GREEN}✅ SysMho Hunter detenido correctamente${CYAN}   ║"
echo -e "  ║                                              ║"
echo -e "  ║  ${NC}Para reiniciar:  ${BOLD}./start.sh${NC}${CYAN}                 ║"
echo -e "  ╚══════════════════════════════════════════════╝${NC}"
echo ""
