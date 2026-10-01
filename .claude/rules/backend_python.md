# Python — Reglas (CLI)

## Gestión de Dependencias
- **uv siempre:** Nunca `pip install`. Usar `uv add`, `uv sync`, `uv run`
- Todas las dependencias en `pyproject.toml` (raíz), nunca hardcodeadas
- Verificar compatibilidad de versiones antes de agregar nuevas deps

## Código Python

### PEP8 & Linting
- Todo código Python **DEBE** pasar `uv run ruff check code/` sin errores
- Ejecutar `uv run ruff format code/` antes de cada commit
- Line length máximo: 79 caracteres (configurado en pyproject.toml)

### Async/Await
- **Async-first:** cualquier función que toque red o procesos externos → `async def`
- Nunca bloquear el event loop con operaciones sincrónicas
- Usar `asyncio.create_subprocess_exec` con timeout para subprocesos
- Nunca `subprocess.run` síncrono

### Estructura
- Código en `code/` (brain/, rag/, recon/, core/, cli/)
- Config centralizada en `code/config.py` (`pydantic-settings`)
- Evidencia en archivos locales (`output/<target>/<fecha>/`), nunca BD

### Seguridad
- **Secretos en .env:** todas las claves via `pydantic-settings`, NUNCA en código
- Documentar nuevas vars en `.env.example`
- **Scope enforcement:** `BaseTool._validate_scope()` antes de ejecutar herramientas
- Payloads no destructivos hasta aprobación explícita

### Paths & Configuración
- Nunca hardcodear paths absolutos en código
- Usar `settings.` para acceder a config centralizada
- Variables de entorno via `pydantic-settings`

## Testing
- Tests en `tests/` con pytest (pytest-asyncio)
- Sin base de datos: los tests no dependen de servicios externos
- Los tests que invocan el cerebro requieren Ollama/Gemini disponibles
- Ejecutar antes de commit: `uv run pytest tests/ -v`
