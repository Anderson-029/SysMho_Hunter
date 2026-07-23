# AGENTS.md — backend/

## Estructura

```
backend/
├── app/
│   ├── main.py          # FastAPI factory + lifespan (inicia BD, Ollama check, MLEngine)
│   ├── config.py        # pydantic-settings: lee .env, expone Settings singleton
│   ├── database.py      # SQLAlchemy async engine + get_session() dependency
│   ├── api/v1/          # Endpoints REST (targets, scans, findings, reports, actions)
│   ├── models/          # ORM SQLAlchemy (declarative, async compatible) — 12 entidades
│   ├── schemas/         # Pydantic v2 schemas para request/response
│   ├── services/        # Lógica de negocio (ScanService, ReportService)
│   ├── brain/           # Cerebro híbrido 3 niveles
│   ├── rag/             # QdrantStore, embeddings, indexer, retriever (RAG)
│   ├── recon/           # ReconEngine + BaseTool + ToolRegistry + tools/
│   └── websocket/       # /ws/live — stream de logs en tiempo real
├── migrations/          # Alembic (env.py configurado para async SQLAlchemy)
├── pyproject.toml       # uv project
└── .python-version      # 3.12
```

## Endpoints API v1

### Targets (`/api/v1/targets`)
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/` | Lista todos los targets |
| POST | `/` | Crear target nuevo |
| GET | `/{target_id}` | Obtener target con sus scopes |
| PATCH | `/{target_id}` | Actualizar target |
| DELETE | `/{target_id}` | Eliminar target |

### Scans (`/api/v1/scans`)
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/` | Lista últimos 100 scans |
| POST | `/` | Iniciar scan (lanza pipeline en background) |
| GET | `/{scan_id}` | Estado detallado del scan |
| DELETE | `/{scan_id}/cancel` | Cancelar scan activo |

### Findings (`/api/v1/findings`)
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/` | Lista findings (filtros: target_id, scan_id, severity, status) |
| GET | `/{finding_id}` | Finding detallado |
| PATCH | `/{finding_id}` | Actualizar estado/info del finding |

### Reports (`/api/v1/reports`)
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/` | Lista reportes |
| POST | `/` | Crear reporte |
| GET | `/latest` | Último reporte generado |
| GET | `/{report_id}` | Reporte detallado |
| POST | `/{report_id}/generate` | Generar markdown H1 con IA (usa brain Nivel 3) |
| GET | `/{report_id}/markdown` | Obtener markdown generado |
| GET | `/latest/quality-check` | Score de calidad 0-10 del último reporte |

### Actions (`/api/v1/actions`)
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/` | Lista todas las pending_actions |
| GET | `/{action_id}` | Acción detallada con payload |
| POST | `/{action_id}/review` | Aprobar o rechazar acción (`{"decision": "approved"\|"rejected", "comment": "..."}`) |

### Health
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del sistema: BD, MLEngine, Ollama |

## Modelos SQLAlchemy (12 entidades)

| Modelo | Tabla | Descripción |
|--------|-------|-------------|
| `Target` | `targets` | Programas HackerOne a pentestear |
| `Scope` | `scopes` | Dominios/IPs autorizados por target |
| `Scan` | `scans` | Ejecuciones de escaneo (status: pending/running/completed/failed/cancelled) |
| `ScanTask` | `scan_tasks` | Tareas individuales por herramienta CLI |
| `Finding` | `findings` | Vulnerabilidades descubiertas (con ml_severity, ml_confidence) |
| `Evidence` | `evidence` | Screenshots, requests, logs adjuntos a findings |
| `PendingAction` | `pending_actions` | Operaciones de riesgo esperando aprobación humana |
| `Report` | `reports` | Reportes H1 en formato Markdown |
| `ReportFinding` | `report_findings` | M2M Reports ↔ Findings |
| `AgentLog` | `agent_logs` | Stream de logs del pipeline (broadcast via WebSocket) |
| `BrainReasoning` | `brain_reasoning` | Auditoría de cada decisión del cerebro híbrido |
| `AgentConfig` | `agent_config` | Configuración clave-valor, modificable en caliente |

## Comandos Frecuentes

```bash
# Instalar dependencias
uv sync

# Ejecutar backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Migraciones
uv run alembic revision --autogenerate -m "descripcion"
uv run alembic upgrade head

# Tests
uv run pytest ../tests/ -v

# Linting
uv run ruff check app/
uv run ruff format app/

# Sembrar agent_config inicial
bash ../scripts/seed_db.sh
```

## Convenciones

- Todos los modelos SQLAlchemy en `app/models/`, uno por entidad, heredan de `Base`
- Schemas Pydantic en `app/schemas/`, separar `Create`, `Update`, `Response`
- Servicios en `app/services/`, inyectan `AsyncSession` via dependency injection
- Routers en `app/api/v1/`, prefijo `/api/v1`
- WebSocket en `app/websocket/router.py`, prefijo `/ws`
- PKs: UUID v4 generados por PostgreSQL (`gen_random_uuid()`)
- Timestamps: `created_at` y `updated_at` con `DEFAULT NOW()` en BD

## RAG (`app/rag/`)

| Componente | Responsabilidad |
|-----------|-----------------|
| `qdrant_client.py` | `QdrantStore`: colección `security_knowledge`, upsert/search de vectores |
| `embeddings.py` | `EmbeddingClient`: wrapper async OpenAI-compatible `/embeddings` |
| `indexer.py` | Parser de Markdown+frontmatter (`knowledge/*.md`) → chunking por sección `##` → indexación |
| `retriever.py` | `retrieve(query)` + `format_context()` — usado por `BrainRouter` en Nivel 2/3 |

Indexar contenido: `cd backend && uv run python ../scripts/ingest_knowledge.py`

**Regla:** RAG es siempre *best-effort*. Si Qdrant no responde, el cerebro
debe seguir funcionando sin contexto — nunca debe lanzar una excepción que
rompa el pipeline de análisis (ver `try/except` en `BrainRouter._fetch_rag_context`).

## Agent Config — Valores Clave

La tabla `agent_config` controla el comportamiento en caliente (no requiere restart):

| Key | Default | Descripción |
|-----|---------|-------------|
| `brain.ml_confidence_threshold` | `0.85` | Umbral para delegar de ML → Ollama |
| `brain.local_llm_confidence_threshold` | `0.70` | Umbral para delegar de Ollama → Cloud |
| `brain.active_brain` | `"auto"` | Forzar nivel: auto/ml/local/cloud |
| `recon.max_concurrent_tools` | `5` | Herramientas en paralelo por scan |
| `recon.default_timeout` | `300` | Timeout en segundos por herramienta |
| `recon.default_phases` | `[...]` | Fases activas por defecto |
| `scope.strict_mode` | `false` | Bloquear targets no en scopes table |
| `actions.auto_approve_low_risk` | `false` | Auto-aprobar risk_level=low |
| `report.h1_min_quality_score` | `7` | Score mínimo para marcar como listo |
