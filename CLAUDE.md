# CLAUDE.md — SysMho Hunter

> Instrucciones maestras para Claude Code al trabajar en este proyecto.
> Tienen prioridad sobre el comportamiento por defecto.

---

## Identidad del Proyecto

**SysMho Hunter v0.4.0** — Agente autónomo de pentesting por **línea de comandos**.

Herramienta CLI conversacional: orquesta un arsenal de reconocimiento, razona
sobre los hallazgos con un cerebro híbrido de IA, y entrega reportes en prosa
en la terminal. Modelada sobre el patrón de `SysMho_Venom` (CLI, evidencia en
archivos locales, sin servidor ni base de datos).

- **Lenguaje:** Python 3.12+, async-first, gestionado con `uv`
- **Cerebro:** híbrido 3 niveles — scikit-learn → Ollama Llama 3.1 8B → Gemini
- **RAG:** Qdrant (Docker) + embeddings `nomic-embed-text` (Ollama)
- **Arsenal:** 19 herramientas CLI (nmap, nuclei, ffuf, sqlmap, subfinder, etc.)
- **Persistencia:** archivos locales en `output/<target>/<fecha>/` — NO hay BD

> **Importante:** este proyecto NO es una app web. No tiene FastAPI, React,
> PostgreSQL, JWT ni endpoints REST. Fue reestructurado desde una versión web
> previa a una herramienta CLI pura. No reintroducir esas capas.

---

## 🎯 5 Pilares (aplican a TODO el código)

1. **Coherencia** — patrones uniformes, sin contradicciones
2. **Congruencia** — specs, implementación y docs alineados
3. **Funcionalidad** — cada feature funciona exactamente como se define
4. **Estabilidad** — cero crashes, degradación elegante si falta un servicio
5. **Seguridad Total** — scope enforcement obligatorio, payloads no destructivos

---

## Reglas Críticas de Desarrollo

### Python / CLI
- **uv siempre:** nunca `pip install`. Usar `uv add`, `uv sync`, `uv run`.
- **Async-first:** toda función que toque red o procesos externos → `async def`.
- **PEP8:** todo código debe pasar `uv run ruff check code/` sin errores. Line-length 79.
- **Subprocess async:** `asyncio.create_subprocess_exec` con timeout. Nunca síncrono.
- **Paths relativos:** nunca hardcodear paths absolutos.
- **Secretos en .env:** `GEMINI_API_KEY` vía `pydantic-settings`. Nunca en código.

### Seguridad / Pentesting
- **Scope enforcement OBLIGATORIO:** los objetivos vienen SIEMPRE de `scope.txt`,
  nunca hardcodeados. `BaseTool._validate_scope()` se verifica antes de cada tool.
- **Aprobación humana:** el agente propone cada herramienta; el usuario aprueba
  antes de que se ejecute. Riesgo medium/high/critical SIEMPRE pide confirmación.
- **Payloads no destructivos por defecto:** sqlmap con `--level=1 --risk=1`.
- **Confirmación de autorización:** registrada en `session.log` al inicio.

### Alcance de la herramienta
- Es un **agente de pentesting genérico** para auditorías autorizadas.
  No referenciar plataformas o programas específicos de bug bounty en código,
  prompts, docs ni mensajes de UI.

---

## Estructura del Proyecto

```
SysMho_Hunter/
├── hunter.py                → wrapper de arranque desde la raíz
├── scope.txt                → objetivos autorizados (plantilla)
├── pyproject.toml           → deps CLI (uv)
├── .env / .env.example      → GEMINI_API_KEY, config Ollama/Qdrant
├── code/
│   ├── hunter.py            → entry point (argparse: -I / directo)
│   ├── config.py            → config CLI (pydantic-settings)
│   ├── ui_utils.py          → banner, colores, prompts
│   ├── session_logger.py    → log JSON de sesión
│   ├── cli/
│   │   ├── interactive.py   → modo guiado -I
│   │   └── render.py        → prosa conversacional + report.md
│   ├── core/
│   │   ├── scope.py         → carga/valida scope.txt + confirmación
│   │   ├── output.py        → output/<target>/<fecha>/
│   │   └── orchestrator.py  → pipeline recon→cerebro→reporte
│   ├── brain/               → cerebro híbrido 3 niveles + RAG query
│   ├── rag/                 → Qdrant + embeddings
│   └── recon/               → ReconEngine, BaseTool, tools/ (19)
├── knowledge/               → knowledge base (RAG)
├── ml/                      → modelos scikit-learn (.pkl)
├── scripts/                 → check_tools, install_tools, ingest_knowledge, test_brain
└── output/                  → evidencia por sesión (gitignored)
```

---

## Comandos Frecuentes

```bash
# Dependencias
uv sync

# Ejecutar el CLI
sudo python3 hunter.py -I                              # interactivo
sudo python3 hunter.py <target> --scope scope.txt      # directo
uv run python hunter.py --help

# Lint + formato
uv run ruff check code/ && uv run ruff format code/

# Tests
uv run pytest tests/ -v

# Cerebro
uv run python scripts/test_brain.py

# RAG — indexar knowledge base
docker compose up -d qdrant
uv run python scripts/ingest_knowledge.py

# Arsenal
bash scripts/check_tools.sh
```

---

## Cerebro Híbrido — 3 Niveles

```
Nivel 1: MLEngine (scikit-learn, <10ms)      → classify_severity, score_vuln, prioritize
Nivel 2: LocalLLM (Llama 3.1 8B, Ollama)     → detect_patterns, reason_next_steps
Nivel 3: CloudClient (Gemini 2.0 Flash)      → tareas complejas, fallback
```

Umbrales hardcodeados en `code/brain/router.py`:
- `ML_CONFIDENCE_THRESHOLD = 0.85`
- `LOCAL_CONFIDENCE_THRESHOLD = 0.70`

Niveles 2/3 reciben contexto de RAG (`code/rag/retriever.py`), best-effort:
si Qdrant no responde, el cerebro sigue sin contexto (nunca bloquea).

---

## Flujo End-to-End

```
1. Cargar scope.txt         → objetivos autorizados
2. Confirmar autorización   → registrado en session.log
3. Elegir objetivo (en scope)
4. Recon por fases          → el agente propone cada tool, usuario aprueba
5. Análisis con el cerebro  → propone próximos pasos
6. Reporte conversacional   → output/<target>/<fecha>/report.md
```

---

## Guía de Debugging

| Síntoma | Dónde mirar |
|---------|-------------|
| El CLI no arranca | `uv sync`, revisar `code/hunter.py` imports |
| Target rechazado | `scope.txt` + `code/core/scope.py` |
| Tool no se ejecuta | `bash scripts/check_tools.sh` (¿instalada?) |
| Cerebro usa nivel incorrecto | `code/brain/router.py` (umbrales) |
| RAG no da contexto | `docker compose up -d qdrant` + `ingest_knowledge.py` |
| Reporte vacío | `code/cli/render.py`, revisar `findings.json` |
| Ver qué pasó en una sesión | `output/<target>/<fecha>/session.log` |
