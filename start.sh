#!/usr/bin/env bash
# ============================================================
# SysMho Hunter - Script de Inicio
# Orquesta el arranque de todos los servicios en orden:
# 1. Verificar PostgreSQL
# 2. Activar venv + iniciar Backend (FastAPI)
# 3. Iniciar Frontend (Vite)
# 4. Abrir navegador
# ============================================================

set -e

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # Sin color
BOLD='\033[1m'

# Directorio base del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE_DIR="${PROJECT_DIR}/.pids"
BACKEND_PID_FILE="${PIDFILE_DIR}/backend.pid"
FRONTEND_PID_FILE="${PIDFILE_DIR}/frontend.pid"
LOG_DIR="${PROJECT_DIR}/logs"

# Banner
echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║       🎯 SysMho Hunter - Iniciando...       ║"
echo "  ║     Agente de IA para Pentesting Web         ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# Crear directorios necesarios
mkdir -p "${PIDFILE_DIR}" "${LOG_DIR}"

# ─────────────────────────────────────────────
# Paso 1: Verificar PostgreSQL
# ─────────────────────────────────────────────
echo -e "${YELLOW}[1/4]${NC} Verificando PostgreSQL..."

if ! command -v pg_isready &> /dev/null; then
    echo -e "${RED}  ✖ pg_isready no encontrado. ¿PostgreSQL está instalado?${NC}"
    exit 1
fi

if pg_isready -h 127.0.0.1 -U postgres &> /dev/null; then
    echo -e "${GREEN}  ✔ PostgreSQL está corriendo${NC}"
else
    echo -e "${YELLOW}  ⚠ PostgreSQL no responde. Intentando iniciar...${NC}"
    sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null
    sleep 2
    if pg_isready -h 127.0.0.1 -U postgres &> /dev/null; then
        echo -e "${GREEN}  ✔ PostgreSQL iniciado correctamente${NC}"
    else
        echo -e "${RED}  ✖ No se pudo iniciar PostgreSQL. Inícialo manualmente.${NC}"
        exit 1
    fi
fi

# Verificar que la base de datos existe
if PGPASSWORD=ander123 psql -U postgres -h 127.0.0.1 -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw sysmho_hunter; then
    echo -e "${GREEN}  ✔ Base de datos 'sysmho_hunter' encontrada${NC}"
else
    echo -e "${YELLOW}  ⚠ Base de datos no encontrada. Creándola...${NC}"
    PGPASSWORD=ander123 psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE sysmho_hunter;" 2>/dev/null
fi

echo -e "${YELLOW}  ♻ Cargando esquema modular...${NC}"
PGPASSWORD=ander123 psql -U postgres -h 127.0.0.1 -d sysmho_hunter -f "${PROJECT_DIR}/database/01_types.sql" 2>/dev/null
PGPASSWORD=ander123 psql -U postgres -h 127.0.0.1 -d sysmho_hunter -f "${PROJECT_DIR}/database/02_tables.sql" 2>/dev/null
PGPASSWORD=ander123 psql -U postgres -h 127.0.0.1 -d sysmho_hunter -f "${PROJECT_DIR}/database/03_functions.sql" 2>/dev/null
PGPASSWORD=ander123 psql -U postgres -h 127.0.0.1 -d sysmho_hunter -f "${PROJECT_DIR}/database/04_triggers.sql" 2>/dev/null
PGPASSWORD=ander123 psql -U postgres -h 127.0.0.1 -d sysmho_hunter -f "${PROJECT_DIR}/database/05_init_data.sql" 2>/dev/null
echo -e "${GREEN}  ✔ Esquema modular cargado correctamente${NC}"

# ─────────────────────────────────────────────
# Paso 2: Verificar que no hay instancias previas corriendo
# ─────────────────────────────────────────────
if [ -f "${BACKEND_PID_FILE}" ] && kill -0 "$(cat "${BACKEND_PID_FILE}")" 2>/dev/null; then
    echo -e "${YELLOW}  ⚠ Backend ya está corriendo (PID $(cat "${BACKEND_PID_FILE}"))${NC}"
    echo -e "${YELLOW}    Ejecuta ${BOLD}./stop.sh${NC}${YELLOW} primero si quieres reiniciar.${NC}"
    exit 1
fi

if [ -f "${FRONTEND_PID_FILE}" ] && kill -0 "$(cat "${FRONTEND_PID_FILE}")" 2>/dev/null; then
    echo -e "${YELLOW}  ⚠ Frontend ya está corriendo (PID $(cat "${FRONTEND_PID_FILE}"))${NC}"
    echo -e "${YELLOW}    Ejecuta ${BOLD}./stop.sh${NC}${YELLOW} primero si quieres reiniciar.${NC}"
    exit 1
fi

# ─────────────────────────────────────────────
# Paso 3: Iniciar Backend (FastAPI en venv)
# ─────────────────────────────────────────────
echo -e "${YELLOW}[2/4]${NC} Iniciando Backend (FastAPI)..."

if [ ! -d "${PROJECT_DIR}/venv" ]; then
    echo -e "${YELLOW}  ⚠ Entorno virtual no encontrado. Creándolo...${NC}"
    python3 -m venv "${PROJECT_DIR}/venv"
    source "${PROJECT_DIR}/venv/bin/activate"
    pip install -r "${PROJECT_DIR}/requirements.txt" --quiet
else
    source "${PROJECT_DIR}/venv/bin/activate"
fi

# Iniciar uvicorn en background
cd "${PROJECT_DIR}"
nohup "${PROJECT_DIR}/venv/bin/uvicorn" main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload \
    > "${LOG_DIR}/backend.log" 2>&1 &
BACKEND_PID=$!
echo "${BACKEND_PID}" > "${BACKEND_PID_FILE}"

# Esperar a que el backend esté listo
echo -n "  Esperando backend"
for i in $(seq 1 15); do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}  ✔ Backend corriendo en http://127.0.0.1:8000 (PID ${BACKEND_PID})${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo ""
    echo -e "${RED}  ✖ Backend no respondió a tiempo. Revisa ${LOG_DIR}/backend.log${NC}"
    kill "${BACKEND_PID}" 2>/dev/null
    rm -f "${BACKEND_PID_FILE}"
    exit 1
fi

# ─────────────────────────────────────────────
# Paso 4: Iniciar Frontend (Vite + React)
# ─────────────────────────────────────────────
echo -e "${YELLOW}[3/4]${NC} Iniciando Frontend (Vite + React)..."

cd "${PROJECT_DIR}/frontend"

# Verificar que node_modules existe
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}  ⚠ node_modules no encontrado. Instalando dependencias...${NC}"
    npm install --silent 2>/dev/null
fi

nohup npx vite --host 0.0.0.0 --port 5173 \
    > "${LOG_DIR}/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "${FRONTEND_PID}" > "${FRONTEND_PID_FILE}"

# Esperar a que el frontend esté listo
echo -n "  Esperando frontend"
for i in $(seq 1 10); do
    if curl -s http://127.0.0.1:5173 > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}  ✔ Frontend corriendo en http://localhost:5173 (PID ${FRONTEND_PID})${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s http://127.0.0.1:5173 > /dev/null 2>&1; then
    echo ""
    echo -e "${YELLOW}  ⚠ Frontend tardó en responder. Puede necesitar unos segundos más.${NC}"
fi

# ─────────────────────────────────────────────
# Paso 5: Abrir navegador
# ─────────────────────────────────────────────
echo -e "${YELLOW}[4/4]${NC} Abriendo navegador..."

sleep 1

# Detectar comando para abrir navegador
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:5173" &>/dev/null &
elif command -v open &> /dev/null; then
    open "http://localhost:5173" &>/dev/null &
else
    echo -e "${YELLOW}  ⚠ No se pudo abrir el navegador automáticamente.${NC}"
    echo -e "${YELLOW}    Abre manualmente: ${BOLD}http://localhost:5173${NC}"
fi

# ─────────────────────────────────────────────
# Resumen final
# ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}  ╔══════════════════════════════════════════════╗"
echo -e "  ║     ${GREEN}✅ SysMho Hunter está listo!${CYAN}              ║"
echo -e "  ╠══════════════════════════════════════════════╣"
echo -e "  ║  ${NC}🌐 Dashboard:  ${BOLD}http://localhost:5173${NC}${CYAN}       ║"
echo -e "  ║  ${NC}📡 API:        ${BOLD}http://127.0.0.1:8000${NC}${CYAN}       ║"
echo -e "  ║  ${NC}📖 API Docs:   ${BOLD}http://127.0.0.1:8000/docs${NC}${CYAN}  ║"
echo -e "  ║  ${NC}🗄️  DB:         ${BOLD}sysmho_hunter (PostgreSQL)${NC}${CYAN} ║"
echo -e "  ╠══════════════════════════════════════════════╣"
echo -e "  ║  ${NC}Para detener:  ${BOLD}./stop.sh${NC}${CYAN}                   ║"
echo -e "  ╚══════════════════════════════════════════════╝${NC}"
echo ""
