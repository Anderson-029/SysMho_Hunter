# CLAUDE.md — SysMho Hunter

> Instrucciones maestras para Claude Code al trabajar en este proyecto.
> Estas reglas tienen prioridad sobre el comportamiento por defecto.

---

## Identidad del Proyecto

**SysMho Hunter v0.2.0** — Agente autónomo de pentesting y bug bounty para HackerOne.

- **Backend:** FastAPI + SQLAlchemy async + asyncpg + PostgreSQL, gestionado con `uv`
- **Frontend:** React 19 + Vite + TypeScript + Tailwind CSS + Zustand
- **Cerebro:** Híbrido 3 niveles — scikit-learn → Ollama Llama 3.1 8B Q6_K → Gemini 2.0 Flash
- **Arsenal:** 19 herramientas CLI (nmap, nuclei, ffuf, sqlmap, subfinder, amass, etc.)
- **BD:** PostgreSQL, 12 tablas con UUID como PKs

---

## 🎯 Premisa Principal

**SysMho Hunter debe cumplir con COHERENCIA, CONGRUENCIA, FUNCIONALIDAD, ESTABILIDAD y SEGURIDAD TOTAL.**

Cada línea de código, cada decisión arquitectónica, cada feature debe adherir a estos 5 pilares:

1. **Coherencia** — Código consistente, patrones uniformes, sin contradicciones
2. **Congruencia** — Todo alineado: especificaciones, implementación, documentación
3. **Funcionalidad** — Cada feature funciona exactamente como se define, sin edge cases no manejados
4. **Estabilidad** — Cero crashes, manejo robusto de errores, graceful degradation
5. **Seguridad Total** — Cero vulnerabilidades conocidas, defensa en profundidad, auditoría completa

**Aplicar a TODO:**
- ✅ Código nuevo → pasar los 5 pilares antes de merge
- ✅ Refactoring → mantener o mejorar los 5 pilares
- ✅ Bug fixes → nunca introducir nuevos issues en otros 4 pilares
- ✅ Docs → estar siempre alineadas con código real

---

## Reglas Críticas de Desarrollo

### Python / Backend
- **uv siempre:** nunca `pip install`. Agregar deps con `uv add`, instalar con `uv sync`, ejecutar con `uv run`.
- **Async-first:** toda función que toque BD, red o procesos externos → `async def`. Nunca bloquear el event loop.
- **PEP8 obligatorio:** todo código Python debe pasar `uv run ruff check` sin errores. Ejecutar antes de commit.
- **Paths relativos:** nunca hardcodear paths absolutos en código fuente.
- **Secretos en .env:** todas las claves via `pydantic-settings`. Nuevas vars → documentar en `.env.example`. Nunca en código.
- **Subprocess async:** usar `asyncio.create_subprocess_exec` con timeout 300s. Nunca `subprocess.run` síncrono.

### Seguridad / Pentesting
- **Scope enforcement:** `BaseTool._validate_scope()` DEBE verificarse antes de ejecutar cualquier herramienta. Nunca hardcodear targets.
- **Acciones destructivas:** operaciones con `risk_level=high/critical` → guardar en `pending_actions` y esperar aprobación humana.
- **Payloads no destructivos:** sqlmap con `--level=1 --risk=1` hasta aprobación explícita.
- **Scope de targets:** los targets SIEMPRE vienen de la tabla `scopes` en BD. Nunca de variables hardcodeadas.

### Base de Datos
- **Modelos en `app/models/`**, uno por entidad, herencia de `Base`.
- **Schemas Pydantic en `app/schemas/`**: separar `Create`, `Update`, `Response`.
- **Servicios en `app/services/`**: inyectar `AsyncSession` via dependency injection.
- **Migraciones con Alembic**: `uv run alembic revision --autogenerate -m "descripcion"`.

---

## Procesos y Puertos

| Proceso | Puerto | Comando de arranque |
|---------|--------|---------------------|
| Backend API (FastAPI) | 8000 | `cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Frontend UI (React+Vite) | 5173 | `cd frontend && npm run dev` |
| PostgreSQL | 5432 | `sudo systemctl start postgresql` |
| Ollama (LLM local) | 11434 | `ollama serve` |

**Arranque completo:** `bash scripts/start_hunter.sh`
**Parada completa:** `bash scripts/stop_hunter.sh`

---

## Comandos Frecuentes

```bash
# Backend
cd backend
uv sync                                          # instalar deps
uv run uvicorn app.main:app --reload             # arrancar
uv run alembic upgrade head                      # migraciones
uv run ruff check app/ && uv run ruff format app/ # lint + formato
uv run pytest ../tests/ -v                       # tests

# Frontend
cd frontend
npm run dev       # arrancar
npm run build     # build producción
npx tsc --noEmit  # verificar TypeScript

# Herramientas
bash scripts/install_tools.sh  # instalar arsenal CLI
bash scripts/seed_db.sh        # sembrar agent_config inicial
```

---

## Cerebro Híbrido — 3 Niveles

```
Nivel 1: MLEngine (scikit-learn, <10ms)          → classify_severity, score_vuln, prioritize
Nivel 2: LocalLLM (Llama 3.1 8B Q6_K, Ollama)   → detect_patterns, analyze_response
Nivel 3: CloudClient (Gemini 2.0 Flash) → draft_report, tareas complejas
```

Umbrales configurables en BD (`agent_config`):
- `brain.ml_confidence_threshold` (default: 0.85)
- `brain.local_llm_confidence_threshold` (default: 0.70)

---

## Módulos — Dónde Está Cada Cosa

| Módulo | Path | Responsabilidad |
|--------|------|----------------|
| API REST | `backend/app/api/v1/` | Endpoints: targets, scans, findings, reports, actions |
| Modelos ORM | `backend/app/models/` | 12 tablas: targets, scopes, scans, scan_tasks, findings, evidence, pending_actions, reports, report_findings, agent_logs, brain_reasoning, agent_config |
| Servicios | `backend/app/services/` | ScanService (pipeline 4 fases), ReportService (H1 markdown) |
| Cerebro | `backend/app/brain/` | BrainRouter, MLEngine, LocalLLM, CloudClient, prompts |
| Arsenal | `backend/app/recon/` | ReconEngine, BaseTool, ToolRegistry, 19 tools |
| WebSocket | `backend/app/websocket/` | `/ws/live` — stream de logs en tiempo real |
| Frontend | `frontend/src/` | components/, stores/ (Zustand), api/, types/ |
| Tests | `tests/` | pytest-asyncio, BD de tests separada |
| Scripts | `scripts/` | start, stop, dev, install_tools, seed_db |

---

## Índice de Skills

| Skill | Descripción | Cuándo usarla |
|-------|-------------|---------------|
| `/hunter` | Panel diagnóstico maestro | Vista rápida del estado completo |
| `/hunter-deploy` | Arranque controlado del sistema | Iniciar SysMho Hunter de forma segura |
| `/hunter-scan` | Vista táctica de scans activos | Revisar operaciones en curso |
| `/hunter-findings` | Vista ofensiva de hallazgos | Evaluar resultados de un scan |
| `/hunter-brain` | Estado del cerebro híbrido | Evaluar rendimiento IA |
| `/hunter-recon` | Arsenal instalado vs pendiente | Antes de planificar expansión |
| `/hunter-scope` | Targets y scopes autorizados | Antes de lanzar un scan |
| `/hunter-actions` | Gestión de pending_actions | Aprobar/rechazar operaciones de riesgo |
| `/hunter-config` | Config del agente en caliente | Ajustar umbrales sin reiniciar |
| `/hunter-logs` | Últimos logs del sistema | Debugging de comportamiento inesperado |
| `/hunter-stats` | Dashboard estadístico | Vista ejecutiva del rendimiento |
| `/hunter-report` | Generar reporte HackerOne | Antes de submitear a H1 |
| `/hunter-ci` | Pipeline CI local | Siempre antes de git commit |
| `/hunter-quality` | Auditoría calidad backend | Score 0-100 antes de commit |
| `/hunter-security` | Escaneo SAST del código | Antes de push |
| `/hunter-owasp` | Auditoría OWASP Top 10 + MITRE ATT&CK + CWE | **Antes de operar contra targets reales** |
| `/hunter-ui-audit` | Auditoría frontend | Evaluar dependencias UI |
| `/hunter-ui-upgrade` | Instalar deps pro UI | Después de audit con score < 10 |
| `/hunter-prompt-improver` | Optimizar prompt antes de tarea compleja | Cualquier tarea ambigua |

---

## Guía de Debugging Rápido

| Síntoma | Skill a usar | Archivo/Módulo |
|---------|-------------|----------------|
| Sistema no arranca | `/hunter-deploy` | `scripts/start_hunter.sh` |
| Scan no avanza / falla | `/hunter-scan` → `/hunter-logs` | `backend/app/services/scan_service.py` |
| Cerebro usa nivel incorrecto | `/hunter-brain` | `backend/app/brain/router.py` |
| Operación bloqueada (high risk) | `/hunter-actions` | `backend/app/api/v1/actions.py` |
| Herramienta no encontrada | `/hunter-recon` | `backend/app/recon/tool_registry.py` |
| Target fuera de scope | `/hunter-scope` | `backend/app/recon/base_tool.py` |
| Reporte H1 con baja calidad | `/hunter-findings` → `/hunter-report` | `backend/app/services/report_service.py` |
| Error de BD | `/hunter` → `/hunter-stats` | `backend/app/database.py` |
| Umbral cerebro incorrecto | `/hunter-config` | tabla `agent_config` |
| Tests fallando | `tests/AGENTS.md` | `cd backend && uv run pytest ../tests/ -v` |
| Auditoría previa a operación | `/hunter-owasp` | OWASP + MITRE + CWE completo |

---

## Flujo End-to-End (Referencia Rápida)

```
1. /hunter-scope        → confirmar target autorizado
2. POST /api/v1/scans   → lanzar scan
3. /hunter-scan         → monitorear progreso
4. /hunter-actions      → aprobar si hay pending_actions
5. /hunter-findings     → revisar resultados
6. /hunter-report       → generar y revisar reporte H1
```
