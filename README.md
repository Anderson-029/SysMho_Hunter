# SysMho Hunter

**v0.3.0-dev** — Agente autónomo de pentesting y bug bounty orientado a HackerOne.

Automatiza reconocimiento, análisis de vulnerabilidades y generación de reportes, con un cerebro híbrido (ML → LLM local → cloud) y enforcement estricto de scope.

> Solo usar contra targets autorizados. El scope vive en la base de datos; las operaciones de riesgo alto/crítico requieren aprobación humana (`pending_actions`).

---

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy async, Alembic, `uv` |
| Frontend | React 19, Vite, TypeScript, Tailwind, Zustand |
| BD | PostgreSQL 16 (Docker Compose, puerto host **5433**) |
| RAG | Qdrant v1.13.4 (Docker) + embeddings OpenAI-compatible |
| LLM local | Cualquier servidor OpenAI-compatible (p. ej. [LM Studio](https://lmstudio.ai/)) |
| Cloud | Gemini 2.0 Flash (fallback Nivel 3) |
| Arsenal | nmap, nuclei, ffuf, sqlmap, subfinder, amass, … |

### Cerebro híbrido (3 niveles)

```
Nivel 1  MLEngine (scikit-learn)     → classify / score / prioritize   (<10 ms)
Nivel 2  Local LLM (OpenAI-compat)   → patrones, análisis, siguientes pasos
Nivel 3  Cloud (Gemini)              → reportes y tareas complejas
```

Nivel 2 y 3 reciben contexto RAG desde Qdrant (best-effort: si Qdrant cae, el pipeline sigue).

---

## Requisitos

- Docker + Docker Compose (OrbStack / Docker Desktop)
- [uv](https://docs.astral.sh/uv/) (Python)
- Node.js 20+
- LM Studio (u otro endpoint `/v1`) con un modelo de chat + embeddings
- Herramientas CLI de pentest (ver [`scripts/README_TOOLS.md`](scripts/README_TOOLS.md)) — opcionales al arrancar la UI/API

---

## Arranque rápido

### 1. Clonar y configurar

```bash
git clone <URL_DEL_REPO> SysMho_Hunter
cd SysMho_Hunter

cp .env.example .env                 # vars para docker compose (DB_*)
cp backend/.env.example backend/.env # secrets + LLM — editar valores reales
```

En `backend/.env` como mínimo:

- `DB_PASSWORD`, `API_KEY`, `SECRET_KEY`, `ADMIN_PASSWORD`
- `LOCAL_LLM_BASE_URL=http://localhost:1234/v1`
- `LOCAL_LLM_MODEL=<id del modelo en LM Studio>` (ej. `dolphin3-cyber-8b`)
- `EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5`
- `GEMINI_API_KEY` (opcional; sin ella el Nivel 3 cloud no está disponible)

Guía LLM: [`docs/LM_STUDIO.md`](docs/LM_STUDIO.md)

### 2. Infra Docker (Postgres + Qdrant)

```bash
docker compose up -d
```

| Servicio | Puerto host | Notas |
|----------|-------------|--------|
| PostgreSQL | **5433** → 5432 | Evita choque con Postgres del sistema en `:5432` |
| Qdrant | 6333 / 6334 | Colección `security_knowledge` |

### 3. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
cd .. && bash scripts/seed_db.sh
cd backend && uv run python scripts/create_admin.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. LLM local

1. Abrir LM Studio, cargar el modelo de chat (ej. Dolphin Cyber).
2. Tener disponible el modelo de embeddings Nomic.
3. Activar **Local Server** en `http://127.0.0.1:1234`.

### Arranque / diagnóstico con scripts

```bash
bash scripts/doctor.sh         # estado de bases
bash scripts/start_sysmho.sh   # compose + migraciones + backend + frontend
bash scripts/stop_sysmho.sh
```

| URL | Qué |
|-----|-----|
| http://localhost:5173 | UI |
| http://localhost:8000/docs | OpenAPI (si `DEBUG=true`) |
| http://localhost:8000/health | Health |
| http://localhost:6333/readyz | Qdrant |

---

## Arquitectura (vista rápida)

```
Frontend (Vite :5173)
    │  REST /api/v1 + WS /ws/live
    ▼
Backend (FastAPI :8000)  ──►  LLM local :1234/v1
    │                         (chat + embeddings)
    ├── PostgreSQL :5433
    └── Qdrant :6333  ◄── knowledge/*.md (ingest)
         Arsenal CLI en el host (nmap, nuclei, …)
```

Backend y frontend corren en el **host** (no en Compose). Compose solo levanta infra. El arsenal de pentest necesita red/host nativo; dockerizar la app completa no es el flujo de desarrollo recomendado.

---

## Estructura del repo

```
backend/          API FastAPI, cerebro, RAG, recon, migraciones
frontend/         UI React + Vite
knowledge/        Docs Markdown indexables en Qdrant
ml/               Entrenamiento / modelos scikit-learn (*.pkl no van en git)
scripts/          start, stop, doctor, seed, ingest, tools
docs/             Guías (LM Studio, …)
tests/            pytest-asyncio
docker-compose.yml
```

Documentación adicional:

- [`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md) — reglas del proyecto
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — despliegue en máquina nueva
- [`PENDIENTES.md`](PENDIENTES.md) — roadmap
- [`docs/LM_STUDIO.md`](docs/LM_STUDIO.md) — LLM local

---

## Desarrollo

```bash
# Lint / tests backend
cd backend
uv run ruff check app/
uv run pytest ../tests/ -v

# Typecheck / build frontend
cd frontend
npx tsc --noEmit
npm run build
```

BD de tests: crear `sysmho_hunter_test` en el Postgres de Compose y configurar [`.env.test`](.env.test) (ver `tests/AGENTS.md`).

Indexar knowledge base:

```bash
cd backend && uv run python ../scripts/ingest_knowledge.py
```

Si cambias dimensiones del modelo de embeddings, reindexa Qdrant.

---

## Seguridad (recordatorio)

- Targets y scopes **solo** desde la tabla `scopes`.
- `BaseTool._validate_scope()` antes de ejecutar cualquier tool.
- Riesgo `high` / `critical` → `pending_actions` + aprobación humana.
- sqlmap por defecto `--level=1 --risk=1` hasta aprobación explícita.
- Nunca commitear `backend/.env` ni claves reales.

---

## Licencia / uso

Proyecto en desarrollo (`v0.3.0-dev`). Uso exclusivo en programas de bug bounty / pentest con autorización escrita.
