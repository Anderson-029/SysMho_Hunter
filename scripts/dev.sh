#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Script de desarrollo
# Levanta PostgreSQL, Ollama, backend y frontend
# Los procesos sobreviven al cierre del script (nohup+disown)
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS_DIR="$ROOT/.pids"
mkdir -p "$PIDS_DIR"

echo "=== SysMho Hunter — Iniciando entorno de desarrollo ==="

# 1. PostgreSQL
echo "▶ Verificando PostgreSQL..."
if ! pg_isready -h 127.0.0.1 -p 5432 &>/dev/null; then
    echo "  Iniciando PostgreSQL..."
    sudo systemctl start postgresql
    sleep 2
fi
echo "  ✅ PostgreSQL activo"

# 2. Ollama
echo "▶ Verificando Ollama..."
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "  Iniciando Ollama en background..."
    nohup ollama serve >>/tmp/sysmho_ollama.log 2>&1 &
    disown $!
    echo $! > "$PIDS_DIR/ollama.pid"
    sleep 3
fi
echo "  ✅ Ollama activo"

# 3. Migraciones
echo "▶ Aplicando migraciones..."
cd "$ROOT/backend"
uv run alembic upgrade head 2>/dev/null && echo "  ✅ Migraciones OK"

# 4. Backend
echo "▶ Iniciando backend (puerto 8000)..."
cd "$ROOT/backend"
nohup uv run uvicorn app.main:app \
    --host 0.0.0.0 --port 8000 --reload \
    >>/tmp/sysmho_backend.log 2>&1 &
BACKEND_PID=$!
disown $BACKEND_PID
echo $BACKEND_PID > "$PIDS_DIR/backend.pid"

echo "  Esperando backend..."
for i in $(seq 1 10); do
    sleep 2
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "  ✅ Backend activo (PID: $BACKEND_PID)"
        break
    fi
    if [ "$i" -eq 10 ]; then
        echo "  ⚠️  Backend tardando — revisa: tail -f /tmp/sysmho_backend.log"
    fi
done

# 5. Frontend
echo "▶ Iniciando frontend (puerto 5173)..."
cd "$ROOT/frontend"
nohup npm run dev >>/tmp/sysmho_frontend.log 2>&1 &
FRONTEND_PID=$!
disown $FRONTEND_PID
echo $FRONTEND_PID > "$PIDS_DIR/frontend.pid"
sleep 2
echo "  ✅ Frontend activo (PID: $FRONTEND_PID)"

echo ""
echo "==================================="
echo "  SysMho Hunter está corriendo:"
echo "  UI:       http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health:   http://localhost:8000/health"
echo "==================================="
echo ""
echo "Logs en tiempo real:"
echo "  Backend:  tail -f /tmp/sysmho_backend.log"
echo "  Frontend: tail -f /tmp/sysmho_frontend.log"
echo "  Ollama:   tail -f /tmp/sysmho_ollama.log"
echo ""
echo "Para detener todo: bash $ROOT/scripts/stop.sh"
