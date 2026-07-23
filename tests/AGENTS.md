# AGENTS.md — tests/

## Convenciones

- Framework: `pytest` + `pytest-asyncio`
- BD de tests: PostgreSQL separada (`sysmho_hunter_test`) — NO mockear BD, usar BD real
- Fixtures globales en `conftest.py`
- Mocks: mockear llamadas a herramientas CLI y APIs cloud. No mockear BD.
- Prerequisito: `bash scripts/seed_db.sh` para inicializar `agent_config` en BD de tests

## Comandos

```bash
# Desde la raíz del proyecto
cd backend && uv run pytest ../tests/ -v

# Solo un módulo
uv run pytest ../tests/test_brain/ -v

# Con cobertura
uv run pytest ../tests/ --cov=app --cov-report=term-missing

# Ver score de calidad antes de commit
# (equivalente a /hunter-quality)
uv run ruff check app/ && uv run pytest ../tests/ -v
```

## Estructura

```
tests/
├── conftest.py          # Fixtures: async_session, client HTTP de prueba, mocks de tools
├── test_brain/
│   ├── test_ml_engine.py       # Prueba predicciones ML con datos sintéticos
│   ├── test_brain_router.py    # Prueba fallback entre niveles (ML → Ollama → Cloud)
│   └── test_cloud_client.py    # Prueba fallback Gemini → Claude en RateLimitError
├── test_recon/
│   ├── test_base_tool.py       # Prueba scope validation, timeout, ScopeViolationError
│   └── test_tool_registry.py   # Prueba auto-registro y detección de binarios
└── test_api/
    ├── test_targets.py         # CRUD targets + scopes
    ├── test_scans.py           # Iniciar scan, cancelar, estado
    └── test_findings.py        # Lista, filtros, actualización de findings
```

## BD de Tests

Variable de entorno para apuntar a BD separada:
```bash
TEST_DATABASE_URL=postgresql+asyncpg://postgres:TU_PASSWORD@127.0.0.1/sysmho_hunter_test
```

La BD de tests se crea automáticamente en `conftest.py` con `create_all()` y se limpia entre tests con rollback de transacciones.

## Filosofía de Mocks

| Qué mockear | Qué NO mockear |
|-------------|----------------|
| Binarios CLI (nmap, nuclei, etc.) | Base de datos PostgreSQL |
| Gemini API / Anthropic API | SQLAlchemy async session |
| Ollama HTTP calls / Local LLM | Lógica de negocio propia |
| Filesystem writes de herramientas | Validación de schemas Pydantic |
