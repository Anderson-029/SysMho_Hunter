# AGENTS.md — SysMho Hunter

## Identidad

**SysMho Hunter v0.3.0-dev — Agente Autónomo de Pentesting y Bug Bounty.**

Stack: Python 3.12 + FastAPI + PostgreSQL + React/Vite + uv
Cerebro: Híbrido 3 niveles — scikit-learn → Local LLM OpenAI-compatible → Gemini 2.0 Flash
RAG: Qdrant (Docker) + embeddings OpenAI-compatible — enriquece Nivel 2/3 con contexto técnico
Arsenal: nmap, ffuf, feroxbuster, nuclei, subfinder, amass + herramientas Kali/Parrot
Propósito: Automatizar reconocimiento web, análisis de vulnerabilidades e integración con HackerOne.

---

## Reglas Críticas

- **uv siempre:** nunca `pip install`. Usar `uv add` para agregar deps, `uv sync` para instalar, `uv run` para ejecutar.
- **Async-first:** toda función que toque BD, red o procesos externos → `async def`. No bloquear el event loop.
- **Scope enforcement:** los targets a pentestear vienen de la tabla `scopes` en BD. `BaseTool._validate_scope()` DEBE verificar scope antes de ejecutar cualquier herramienta. Nunca hardcodear targets.
- **Secretos en .env:** todas las claves en `.env` vía `pydantic-settings`. Nuevas vars → documentar en `.env.example`. NUNCA en código.
- **Acciones destructivas:** operaciones con `risk_level=high/critical` → guardar en tabla `pending_actions` y esperar aprobación humana. No ejecutar directamente.
- **Payloads no destructivos por defecto:** sqlmap con `--level=1 --risk=1` hasta aprobación humana explícita.
- **CLI Tools:** usar `asyncio.create_subprocess_exec` con timeout de 300s por defecto. Nunca subprocess síncrono.
- **Paths relativos:** nunca hardcodear paths absolutos en código fuente.

---

## Tres Procesos

| Proceso | Tecnología | Puerto | Comando |
|---------|-----------|--------|---------|
| **Backend API** | FastAPI + uvicorn | 8000 | `cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| **Frontend UI** | React + Vite | 5173 | `cd frontend && npm run dev` |
| **PostgreSQL** | Docker Compose | 5432 | `docker compose up -d` |
| **Local LLM** | LM Studio / Ollama /v1 | 1234 / 11434 | Ver `docs/LM_STUDIO.md` |
| **Qdrant** | Docker Compose | 6333 | `docker compose up -d` |

**Comunicación:**
- HTTP REST: Frontend → `/api/v1/*` endpoints en backend
- WebSocket: Frontend ← `/ws/live` stream de logs en tiempo real
- asyncpg pool: Backend ↔ PostgreSQL
- HTTP: BrainRouter → Local LLM `{LOCAL_LLM_BASE_URL}/chat/completions`
- HTTP: BrainRouter → RAG (`app/rag/retriever.py`) → Qdrant `localhost:6333` (best-effort, no bloqueante)

---

## Cerebro Híbrido — 3 Niveles

```
Nivel 1: MLEngine (scikit-learn, <10ms)          → classify_severity, score_vuln, prioritize
Nivel 2: LocalLLM (OpenAI-compatible)            → detect_patterns, analyze_response
Nivel 3: CloudClient (Gemini 2.0 Flash) → draft_report, tareas complejas
```

Regla: cada nivel intenta → si confianza < umbral → delega al siguiente.
Umbrales configurables en BD: `brain.ml_confidence_threshold` (0.85), `brain.local_llm_confidence_threshold` (0.70).

---

## Índice de Skills (19 skills)

### Operación y Monitoreo
| Skill | Descripción | Path |
|-------|-------------|------|
| `hunter` | Panel diagnóstico maestro: procesos, BD, scans recientes, pending_actions | `.claude/skills/hunter/SKILL.md` |
| `hunter-deploy` | Setup completo: PostgreSQL → migraciones → backend → frontend | `.claude/skills/hunter-deploy/SKILL.md` |
| `hunter-scan` | Vista táctica de scans activos, fase actual, tools corriendo | `.claude/skills/hunter-scan/SKILL.md` |
| `hunter-scope` | Targets y scopes autorizados, violaciones recientes | `.claude/skills/hunter-scope/SKILL.md` |
| `hunter-actions` | Pending_actions pendientes, aprobar/rechazar operaciones de riesgo | `.claude/skills/hunter-actions/SKILL.md` |
| `hunter-logs` | Últimos logs por nivel (ERROR/WARNING/INFO), debugging | `.claude/skills/hunter-logs/SKILL.md` |
| `hunter-config` | Ver y modificar agent_config en caliente (umbrales, timeouts, fases) | `.claude/skills/hunter-config/SKILL.md` |
| `hunter-stats` | Dashboard estadístico: scans, findings, arsenal, cerebro, tokens cloud | `.claude/skills/hunter-stats/SKILL.md` |
| `hunter-performance` | Performance y optimización: latencia, cuellos de botella, costo cloud, recomendaciones | `.claude/skills/hunter-performance/SKILL.md` |

### Análisis de Resultados
| Skill | Descripción | Path |
|-------|-------------|------|
| `hunter-findings` | Vista ofensiva: severidad, críticos, cadenas detectadas | `.claude/skills/hunter-findings/SKILL.md` |
| `hunter-brain` | Estado del cerebro: nivel activo, confianza, últimas decisiones | `.claude/skills/hunter-brain/SKILL.md` |
| `hunter-recon` | Arsenal: tools instaladas vs pendientes, fases disponibles | `.claude/skills/hunter-recon/SKILL.md` |
| `hunter-report` | Generar y previsualizar reporte HackerOne del último scan | `.claude/skills/hunter-report/SKILL.md` |

### Calidad y Seguridad del Código
| Skill | Descripción | Path |
|-------|-------------|------|
| `hunter-ci` | Pipeline CI local: lint, formato, imports, .env check. PASS/FAIL | `.claude/skills/hunter-ci/SKILL.md` |
| `hunter-quality` | Auditoría completa: ruff check + format + imports + tests. Score 0-100 | `.claude/skills/hunter-quality/SKILL.md` |
| `hunter-security` | SAST bandit, secretos hardcodeados, .env en git | `.claude/skills/hunter-security/SKILL.md` |

### Frontend
| Skill | Descripción | Path |
|-------|-------------|------|
| `hunter-ui-audit` | Auditoría frontend: componentes, deps instaladas, score 0-10 | `.claude/skills/hunter-ui-audit/SKILL.md` |
| `hunter-ui-upgrade` | Instala deps pro: recharts, tanstack, framer-motion, lucide-react | `.claude/skills/hunter-ui-upgrade/SKILL.md` |

### Productividad
| Skill | Descripción | Path |
|-------|-------------|------|
| `hunter-prompt-improver` | Optimiza prompts antes de tareas complejas | `.claude/skills/hunter-prompt-improver/SKILL.md` |

---

## Contexto de Módulos

| Archivo | Cubre |
|---------|-------|
| `CLAUDE.md` | Instrucciones maestras, reglas, comandos, guía de debugging completa |
| `backend/AGENTS.md` | Arquitectura backend, entry points, endpoints API, convenciones async |
| `backend/app/brain/AGENTS.md` | Cerebro híbrido 3 niveles, BrainRouter, tareas ML, config hot-reload |
| `backend/app/recon/AGENTS.md` | ReconEngine, BaseTool, ToolRegistry, patrón subprocess async |
| `tests/AGENTS.md` | Fixtures, BD de tests, convenciones pytest-asyncio |

---

## Guía Rápida

| Síntoma | Acción |
|---------|--------|
| El sistema no arranca | `/hunter-deploy` |
| El pipeline no funciona | `/hunter` → `/hunter-scan` → `/hunter-logs` |
| Scan bloqueado (pending_action) | `/hunter-actions` → aprobar/rechazar |
| Quiero ver qué targets tengo | `/hunter-scope` |
| Cerebro usa nivel incorrecto | `/hunter-brain` → `/hunter-config` |
| Quiero agregar herramienta | `backend/app/recon/AGENTS.md` → crear en `tools/` |
| Bug en el cerebro | `/hunter-brain` → `backend/app/brain/AGENTS.md` |
| Tests fallando | `tests/AGENTS.md` → `uv run pytest` |
| Reporte HackerOne | `/hunter-findings` → `/hunter-report` |
| Commit seguro | `/hunter-ci` → `/hunter-security` |
| Ver rendimiento global | `/hunter-stats` |
| Sistema lento / optimizar costos | `/hunter-performance` |
