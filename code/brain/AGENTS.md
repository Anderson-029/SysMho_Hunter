# AGENTS.md — code/brain/

## Arquitectura del Cerebro Híbrido

```
BrainRouter.route(task_type, input_data)
    │
    ▼
[Nivel 1] MLEngine (scikit-learn)
    Umbral confianza: 0.85 (ML_CONFIDENCE_THRESHOLD en router.py)
    ML_TASKS: classify_severity, score_vuln, prioritize_targets
    HYBRID_TASKS: detect_patterns, reason_next_steps (primario)
    │
    ▼ (si confianza < 0.85)
[RAG] rag/retriever.py → Qdrant (best-effort, no bloqueante)
    Enriquece el prompt con contexto de la knowledge base antes de Nivel 2/3.
    Si Qdrant/embeddings fallan, retorna "" y el cerebro sigue sin contexto.
    │
    ▼
[Nivel 2] LocalLLM — Ollama (localhost:11434)
    Modelo: llama3.1:8b-instruct-q6_K
    Umbral confianza: 0.70 (LOCAL_CONFIDENCE_THRESHOLD en router.py)
    Tareas: detect_patterns (fallback), analyze_response, reason_next_steps
    │
    ▼ (si Ollama no disponible o confianza < 0.70)
[Nivel 3] CloudClient — Gemini 2.0 Flash
    Fallback final. Siempre responde o devuelve un dict de error (nunca lanza).
```

## Agentes especializados (Nivel 2)

El Nivel 2 no usa un solo modelo: cada `task_type` se enruta a un **agente**
(rol + system prompt + modelo de Ollama) definido en `agents.py`.

| Agente | Modelo (default) | task_types |
|--------|------------------|------------|
| ReconAnalyzer | `qwen3:14b` | `reason_next_steps` |
| CodeAnalyzer | `qwen2.5-coder:14b` | `analyze_response`, `detect_patterns` |
| ReportWriter | `mistral-small3.2:24b-...` | `draft_report` |
| PayloadCrafter | `dolphin-mixtral:8x7b` | `craft_payload` *(opt-in, bajo aprobación)* |

- Modelos configurables por env (`AGENT_RECON_MODEL`, etc. — ver config.py).
- Equilibrio velocidad/capacidad: 14b para el trabajo frecuente; 24b/mixtral
  solo para tareas puntuales (reporte, payloads).
- `LocalLLM.resolve_model()` degrada al modelo por defecto (`OLLAMA_MODEL`) si
  el modelo del agente no está instalado → estabilidad.
- `router.route()` resuelve el agente vía `agents.resolve_agent(task_type)` y
  pasa su `model` + `system_prompt` a `LocalLLM.complete()`.

## Archivos

| Archivo | Responsabilidad |
|---------|-----------------|
| `router.py` | BrainRouter: orquesta los 3 niveles. Resuelve agente en Nivel 2 |
| `agents.py` | Registro de agentes especializados (rol + modelo + task_types) |
| `ml_engine.py` | MLEngine: carga modelos `.pkl` (lazy, joblib) y clasifica |
| `local_llm.py` | LocalLLM: cliente Ollama multi-modelo (aiohttp, /api/chat) |
| `cloud_client.py` | CloudClient: cliente Gemini (google-genai, import lazy) |
| `prompts.py` | Construcción de prompts + bloque RAG |

## Notas de diseño

- **Sin base de datos.** Los umbrales son constantes en `router.py`, no se leen
  de ninguna tabla. Las decisiones se registran vía `logger` (van a `session.log`).
- **Degradación elegante.** Si faltan modelos ML, Ollama o Gemini, el router
  escala al siguiente nivel disponible; si todos fallan, devuelve un dict de
  error con `brain_level: 0` (nunca lanza excepción al pipeline).
- **RAG es best-effort.** Nunca bloquea el análisis.
