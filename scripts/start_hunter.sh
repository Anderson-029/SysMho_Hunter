#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Start script universal con autocorrecciones
# Inicia: PostgreSQL → Ollama → BD migraciones → Backend → Frontend
# Autocorrige fallos comunes (deps faltantes, puertos ocupados, etc)
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS_DIR="$ROOT/.pids"
mkdir -p "$PIDS_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}▶${NC} $1"; }
log_ok() { echo -e "${GREEN}✅${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠️${NC}  $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  SysMho Hunter — Sistema completo de inicialización║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# 1. PREREQUISITOS — Verificar binarios esenciales
# ============================================================
log_info "Verificando prerequisitos..."

check_command() {
    local cmd="$1"
    local desc="$2"
    if ! command -v "$cmd" &> /dev/null; then
        log_error "$desc no encontrado. Instala: sudo apt-get install $cmd"
        return 1
    fi
}

check_command "python3" "Python 3"
check_command "node" "Node.js"
check_command "psql" "PostgreSQL"
check_command "curl" "curl"

if ! command -v uv &> /dev/null; then
    log_warn "uv no encontrado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.bashrc || true
fi
log_ok "Todos los prerequisitos OK"

echo ""

# ============================================================
# 2. POSTGRESQL — Iniciar y verificar
# ============================================================
log_info "PostgreSQL..."

if ! pg_isready -h 127.0.0.1 -p 5432 &>/dev/null; then
    log_warn "PostgreSQL no responde. Iniciando..."
    if ! sudo systemctl start postgresql 2>/dev/null; then
        log_error "No se pudo iniciar PostgreSQL con systemctl"
        if ! command -v postgres &> /dev/null; then
            log_error "PostgreSQL no está instalado"
            exit 1
        fi
    fi
    sleep 3
    if ! pg_isready -h 127.0.0.1 -p 5432 &>/dev/null; then
        log_error "PostgreSQL aún no responde después de 3s. Estado:"
        sudo systemctl status postgresql 2>/dev/null || echo "  (systemctl no disponible)"
        exit 1
    fi
fi
log_ok "PostgreSQL activo en localhost:5432"

echo ""

# ============================================================
# 3. OLLAMA — Descargar (si no existe) e iniciar
# ============================================================
log_info "Ollama (Llama 3.1 8B)..."

if ! command -v ollama &> /dev/null; then
    log_warn "Ollama no instalado. Descargando..."
    curl -fsSL https://ollama.ai/install.sh | sh
    sleep 2
fi

if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    log_warn "Ollama no responde. Iniciando en background..."
    nohup ollama serve >>/tmp/sysmho_ollama.log 2>&1 &
    OLLAMA_PID=$!
    disown $OLLAMA_PID
    echo $OLLAMA_PID > "$PIDS_DIR/ollama.pid"

    log_warn "Esperando Ollama (máx 15s)..."
    for i in $(seq 1 15); do
        sleep 1
        if curl -s http://localhost:11434/api/tags &>/dev/null; then
            break
        fi
        if [ "$((i % 5))" -eq 0 ]; then
            echo -ne "\r  Intento $i/15..."
        fi
    done
    echo ""
fi

# Verificar que llama3.1:8b-instruct-q6_k existe en Ollama
# Espera a que Ollama responda primero
log_warn "Esperando API de Ollama (máx 10s)..."
for i in $(seq 1 10); do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        break
    fi
    sleep 1
done

# Verificar modelo exacto
if curl -s http://localhost:11434/api/tags | grep -q '"name":"llama3.1:8b-instruct-q6_k"'; then
    log_ok "Modelo Llama 3.1 8B Q6_K ✓ (ya existe)"
else
    log_warn "Modelo no encontrado. Descargando (~7GB, toma ~5-10 min)..."
    if ! ollama pull llama3.1:8b-instruct-q6_k; then
        log_error "Fallo descargando modelo. Revisa: tail -f /tmp/sysmho_ollama.log"
        exit 1
    fi
    log_ok "Modelo descargado"
fi

log_ok "Ollama activo en localhost:11434 con modelo Llama 3.1 8B"

echo ""

# ============================================================
# 4. BACKEND — Dependencias Python + Migraciones
# ============================================================
log_info "Backend (FastAPI)..."

cd "$ROOT/backend"

# Verificar pyproject.toml y uv.lock
if [ ! -f "pyproject.toml" ]; then
    log_error "pyproject.toml no encontrado en backend/"
    exit 1
fi

# Sincronizar dependencias Python
log_warn "Sincronizando dependencias Python (esto toma ~30s)..."
if ! uv sync --all-groups >/dev/null 2>&1; then
    log_error "uv sync falló. Intenta:"
    echo "    cd $ROOT/backend && uv sync --all-groups"
    exit 1
fi
log_ok "Dependencias Python sincronizadas"

# Aplicar migraciones
log_warn "Aplicando migraciones a BD..."
if ! uv run alembic upgrade head 2>/dev/null; then
    log_error "Migraciones fallaron. Intenta:"
    echo "    cd $ROOT/backend && uv run alembic upgrade head"
    exit 1
fi
log_ok "Migraciones aplicadas exitosamente"

# Verificar puerto 8000 disponible
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warn "Puerto 8000 ya en uso. Liberando..."
    pkill -f "uvicorn app.main" || true
    sleep 2
fi

# Iniciar backend
nohup uv run uvicorn app.main:app \
    --host 0.0.0.0 --port 8000 --reload \
    >>/tmp/sysmho_backend.log 2>&1 &
BACKEND_PID=$!
disown $BACKEND_PID
echo $BACKEND_PID > "$PIDS_DIR/backend.pid"

log_warn "Esperando backend (máx 20s)..."
for i in $(seq 1 10); do
    sleep 2
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_ok "Backend activo (PID: $BACKEND_PID)"
        break
    fi
    if [ "$i" -eq 10 ]; then
        log_error "Backend no responde tras 20s. Logs:"
        tail -20 /tmp/sysmho_backend.log
        exit 1
    fi
done

echo ""

# ============================================================
# 5. FRONTEND — Dependencias npm + Dev server
# ============================================================
log_info "Frontend (React Vite)..."

cd "$ROOT/frontend"

# Verificar package.json
if [ ! -f "package.json" ]; then
    log_error "package.json no encontrado en frontend/"
    exit 1
fi

# npm install (solo si falta node_modules)
if [ ! -d "node_modules" ]; then
    log_warn "node_modules no encontrado. Instalando deps npm (~60s)..."
    if ! npm install >/dev/null 2>&1; then
        log_warn "npm install falló con ERESOLVE. Reintentando con --legacy-peer-deps..."
        if ! npm install --legacy-peer-deps >/dev/null 2>&1; then
            log_error "npm install --legacy-peer-deps también falló"
            exit 1
        fi
    fi
    log_ok "Dependencias npm instaladas"
else
    log_ok "node_modules ya existe"
fi

# Verificar puerto 5173 disponible
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warn "Puerto 5173 ya en uso. Liberando..."
    pkill -f "vite" || true
    sleep 2
fi

# Iniciar frontend
nohup npm run dev >>/tmp/sysmho_frontend.log 2>&1 &
FRONTEND_PID=$!
disown $FRONTEND_PID
echo $FRONTEND_PID > "$PIDS_DIR/frontend.pid"

sleep 3
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_ok "Frontend activo (PID: $FRONTEND_PID)"
else
    log_warn "Frontend no escucha en 5173. Puede estar compilando aún..."
fi

echo ""

# ============================================================
# 6. RESUMEN FINAL
# ============================================================
echo "╔════════════════════════════════════════════════════╗"
echo "║           ✅ SysMho Hunter operativo              ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "📍 ACCESO:"
echo "   🌐 Dashboard UI  → http://localhost:5173"
echo "   📚 API Backend   → http://localhost:8000"
echo "   📖 Swagger Docs  → http://localhost:8000/docs"
echo "   💚 Health Check  → http://localhost:8000/health"
echo ""
echo "📋 LOGS EN TIEMPO REAL:"
echo "   Backend   → tail -f /tmp/sysmho_backend.log"
echo "   Frontend  → tail -f /tmp/sysmho_frontend.log"
echo "   Ollama    → tail -f /tmp/sysmho_ollama.log"
echo ""
echo "🛑 PARA DETENER:"
echo "   bash $ROOT/scripts/stop_hunter.sh"
echo ""
echo "⚡ VERIFICACIONES:"
echo "   ✅ PostgreSQL"
echo "   ✅ Ollama + Llama 3.1 8B"
echo "   ✅ Backend (FastAPI)"
echo "   ✅ Frontend (React Vite)"
echo ""

# ============================================================
# 7. ABRIR NAVEGADOR AUTOMÁTICAMENTE
# ============================================================
log_info "Abriendo Dashboard..."

open_browser() {
    local url="$1"

    # Detectar navegador disponible (en orden de preferencia)
    if command -v firefox &> /dev/null; then
        firefox "$url" &
    elif command -v chromium &> /dev/null; then
        chromium "$url" &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "$url" &
    elif command -v google-chrome-stable &> /dev/null; then
        google-chrome-stable "$url" &
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$url" &
    elif command -v open &> /dev/null; then
        open "$url" &
    else
        log_warn "No se pudo detectar navegador. Abre manualmente: $url"
        return
    fi
    sleep 2
    log_ok "Dashboard abierto en navegador predeterminado"
}

open_browser "http://localhost:5173"

echo ""
echo "✨ ¡Sistema listo para usar!"
echo ""
