#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Detiene todos los procesos del entorno
# ============================================================

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS_DIR="$ROOT/.pids"

echo "=== SysMho Hunter — Deteniendo procesos ==="

stop_pid() {
    local name="$1"
    local pidfile="$PIDS_DIR/$2.pid"
    if [ -f "$pidfile" ]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" && echo "  ✅ $name detenido (PID: $pid)"
        else
            echo "  ℹ️  $name ya no estaba corriendo"
        fi
        rm -f "$pidfile"
    fi
}

stop_pid "Backend"  "backend"
stop_pid "Frontend" "frontend"
stop_pid "Ollama"   "ollama"

# Fallback por si acaso
pkill -f "uvicorn app.main" 2>/dev/null && echo "  ✅ uvicorn detenido" || true
pkill -f "vite"              2>/dev/null && echo "  ✅ vite detenido"    || true

echo "Listo."
