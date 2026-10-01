# Testing & Aseguramiento de Calidad

## Testing (pytest)

### Setup
- Tests en `tests/` con `pytest` (+ `pytest-asyncio`, `asyncio_mode=auto`)
- `conftest.py` añade `code/` al `sys.path` (sin BD, sin servidor)
- Mock solo en los límites del sistema (APIs externas); el resto, real

### Reglas
- Ejecutar: `uv run pytest tests/ -v`
- Tests async: funcionan con `asyncio_mode=auto` (no hace falta decorar)
- Los tests que invocan el cerebro (`tests/test_brain/`) requieren Ollama/Gemini
  disponibles; los de scope (`tests/test_recon/`) corren sin servicios

### Estructura
```
tests/
├── test_recon/test_base_tool.py   # scope enforcement (sin red)
├── test_brain/test_brain_router.py # cerebro 3 niveles (requiere servicios)
└── conftest.py                     # pythonpath a code/
```

## Validación de Código

### Antes de Commit
```bash
uv run ruff check code/ tests/    # lint (line-length 79, E/F/W/I)
uv run ruff format code/ tests/   # formato
uv run pytest tests/ -v           # tests
```

### Linting
- **Python:** ruff (line-length=79, select E,F,W,I)
- Config en `pyproject.toml` (`[tool.ruff]`)

## Métricas de Calidad

| Métrica | Target | Tool |
|---------|--------|------|
| Lint | 0 errores | ruff check |
| Formato | consistente | ruff format |
| Tests scope | PASS | pytest |
| Imports | sin crash | smoke test |

## Prueba de los 6 Pilares

Antes de dar algo por listo, verificar:
- **Coherencia:** `ruff check` + `ruff format` limpios
- **Congruencia:** sin refs a capas inexistentes (web/BD); docs ↔ código
- **Estabilidad:** imports sin crash; errores de scope controlados; cerebro degrada
- **Funcionalidad:** CLI arranca, tools registradas, render/output funcionan
- **Seguridad:** scope enforcement bloquea fuera de alcance; sin secrets en código
- **Escalabilidad:** tools/agentes pluggables sin tocar el núcleo

## Testing del Cerebro

```bash
uv run python scripts/test_brain.py
```
Valida los 3 niveles (ML → Ollama/agentes → Gemini) y qué nivel/agente atiende
cada tarea. Requiere Ollama corriendo para el Nivel 2.

## Debugging & Logs

```bash
# Evidencia y ciclo de vida de una sesión
cat output/<target>/<fecha>/session.log      # JSON: decisiones, aprobaciones
cat output/<target>/<fecha>/findings.json
cat output/<target>/<fecha>/report.md
```
