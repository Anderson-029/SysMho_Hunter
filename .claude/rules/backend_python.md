# Backend — Reglas Python

## Gestión de Dependencias
- **uv siempre:** Nunca `pip install`. Usar `uv add`, `uv sync`, `uv run`
- Todas las dependencias en `pyproject.toml`, nunca hardcodeadas
- Verificar compatibilidad de versiones antes de agregar nuevas deps

## Código Python

### PEP8 & Linting
- Todo código Python **DEBE** pasar `uv run ruff check` sin errores
- Ejecutar `uv run ruff format` antes de cada commit
- Line length máximo: 79 caracteres (configurado en pyproject.toml)

### Async/Await
- **Async-first:** Cualquier función que toque BD, red o procesos externos → `async def`
- Nunca bloquear el event loop con operaciones sincrónicas
- Usar `asyncio.create_subprocess_exec` con timeout 300s para subprocesos
- Nunca `subprocess.run` síncrono

### Base de Datos
- Modelos ORM en `app/models/` (uno por archivo)
- Schemas Pydantic en `app/schemas/` (separar Create, Update, Response)
- Servicios en `app/services/` (inyectar AsyncSession via DI)
- Migraciones con Alembic: `uv run alembic revision --autogenerate -m "descripcion"`

### Seguridad
- **Secretos en .env:** Todas las claves via `pydantic-settings`, NUNCA en código
- Documentar nuevas vars en `.env.example`
- **Scope enforcement:** `BaseTool._validate_scope()` antes de ejecutar herramientas
- Payloads no destructivos hasta aprobación explícita

### Paths & Configuración
- Nunca hardcodear paths absolutos en código
- Usar `settings.` para acceder a config centralizada
- Variables de entorno via `pydantic-settings`

## Testing
- Tests unitarios en `tests/` con pytest-asyncio
- Usar BD separada para tests (no la producción)
- Coverage mínimo: 80%
- Ejecutar antes de commit: `uv run pytest ../tests/ -v`
