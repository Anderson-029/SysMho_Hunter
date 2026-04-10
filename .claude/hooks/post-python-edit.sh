#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Post-Python-Edit Hook
# Se ejecuta DESPUÉS de editar o escribir un archivo .py.
# Corre ruff check automáticamente (informativo, nunca bloquea).
# Siempre exit 0.
# ============================================================

# Extraer file_path del JSON de CLAUDE_TOOL_INPUT
FILE=$(echo "$CLAUDE_TOOL_INPUT" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)

# Solo actuar en archivos Python
if [[ "$FILE" != *.py ]]; then
  exit 0
fi

# Solo archivos dentro del backend del proyecto
BACKEND_DIR="/home/anderson/Documentos/programas personales/SysMho_Hunter/backend"

if [[ ! -f "$BACKEND_DIR/pyproject.toml" ]]; then
  exit 0
fi

# Ejecutar ruff check (output conciso)
RESULT=$(cd "$BACKEND_DIR" && uv run ruff check "$FILE" --output-format=concise 2>&1)

if [[ -n "$RESULT" ]]; then
  echo ""
  echo "Ruff check — $(basename "$FILE"):"
  echo "$RESULT"
  echo ""
  echo "(Corrige los errores antes de hacer commit: uv run ruff check app/ --fix)"
fi

exit 0
