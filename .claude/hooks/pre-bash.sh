#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Pre-Bash Hook
# Se ejecuta ANTES de cualquier comando Bash.
# Exit 0 = permitir   |   Exit 2 = bloquear (mensaje a Claude)
# ============================================================

# Extraer el comando del JSON de CLAUDE_TOOL_INPUT
COMMAND=$(echo "$CLAUDE_TOOL_INPUT" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null)

# ----------------------------------------------------------
# BLOQUEO DURO: pip install → debe usar uv add
# ----------------------------------------------------------
if echo "$COMMAND" | grep -qE '\bpip\s+(install|uninstall)\b'; then
  echo ""
  echo "BLOQUEADO: Se detectó 'pip install' en el comando."
  echo ""
  echo "Este proyecto usa uv para gestión de dependencias Python."
  echo ""
  echo "Corrección:"
  echo "  Agregar dep:   uv add <paquete>"
  echo "  Instalar todo: uv sync"
  echo "  Ejecutar:      uv run <comando>"
  echo ""
  exit 2
fi

# ----------------------------------------------------------
# BLOQUEO DURO: python -m pip → también prohibido
# ----------------------------------------------------------
if echo "$COMMAND" | grep -qE 'python\s+-m\s+pip'; then
  echo ""
  echo "BLOQUEADO: Se detectó 'python -m pip'."
  echo "Usa 'uv add <paquete>' en su lugar."
  echo ""
  exit 2
fi

# ----------------------------------------------------------
# ADVERTENCIA: escritura directa en .env
# ----------------------------------------------------------
if echo "$COMMAND" | grep -qE '(echo|printf|cat|tee).*(>>?)\s*\.env(\s|$)'; then
  echo "ADVERTENCIA: Intento de modificación directa de .env."
  echo "Edita .env manualmente o usa el archivo .env.example como referencia."
  echo "Recuerda: .env nunca debe commitearse. Continúa con precaución."
  # Exit 0 — solo advertencia, no bloquea
fi

# ----------------------------------------------------------
# ADVERTENCIA: subprocess.run síncrono en código Python
# ----------------------------------------------------------
if echo "$COMMAND" | grep -qE 'subprocess\.run\s*\('; then
  echo "ADVERTENCIA: Se detectó 'subprocess.run' síncrono."
  echo "SysMho Hunter es async-first. Usa 'asyncio.create_subprocess_exec' con timeout."
  # Exit 0 — solo advertencia
fi

exit 0
