# AGENTS.md — backend/app/brain/

## Arquitectura del Cerebro Híbrido

```
BrainRouter.route(task_type, input_data)
    │
    ▼
[Nivel 1] MLEngine (scikit-learn)
    Umbral confianza: 0.85 (configurable en agent_config → brain.ml_confidence_threshold)
    Tareas ML_TASKS: classify_severity, score_vuln, prioritize_targets
    Tareas HYBRID_TASKS: detect_patterns (primario)
    │
    ▼ (si confianza < 0.85)
[RAG] app/rag/retriever.py → Qdrant (best-effort, no bloqueante)
    Enriquece el prompt con contexto de knowledge base antes de Nivel 2/3
    │
    ▼
[Nivel 2] LocalLLM (OpenAI-compatible — LM Studio / Ollama /v1)
    Umbral confianza: 0.70 (configurable → brain.local_llm_confidence_threshold)
    Tareas: detect_patterns (fallback), analyze_response, reason_next_steps
    │
    ▼ (si Local LLM no disponible o confianza < 0.70)
[Nivel 3] CloudClient
    Proveedor: Gemini 2.0 Flash (google-genai)
    Si cuota agotada → retorna error estructurado, sin crash
    Tareas LLM_TASKS: draft_report, analyze_response, cualquier tarea compleja
```

## RAG — Contexto de Knowledge Base (Nivel 2/3)

`BrainRouter._fetch_rag_context(task_type, input_data)` consulta
`app/rag/retriever.py` **antes** de construir el prompt para Nivel 2/3
(nunca para Nivel 1, que es puramente ML). El query de búsqueda se deriva
según la tarea (`_build_rag_query`): título del target + findings para
`reason_next_steps`, tipo de vuln para `draft_report`, descripción cruda
para `detect_patterns`, body HTTP para `analyze_response`.

El contexto recuperado se inyecta en el prompt vía `prompts.rag_block()`.
Si Qdrant no responde o no hay resultados relevantes (`score < 0.5`), el
contexto es `""` y el cerebro sigue funcionando exactamente igual que sin
RAG — **nunca debe romper el flujo** (ver `try/except Exception` en
`_fetch_rag_context`, deliberadamente amplio porque cualquier fallo de
Qdrant/embeddings debe degradar a "sin contexto", no propagar error).

## Tareas por Categoría

| Categoría | Tareas | Nivel inicial |
|-----------|--------|---------------|
| `ML_TASKS` | classify_severity, score_vuln, prioritize_targets | Nivel 1 |
| `LLM_TASKS` | draft_report, analyze_response | Nivel 2 (nunca ML) |
| `HYBRID_TASKS` | detect_patterns, reason_next_steps | Nivel 1 → fallback a 2/3 |

## Archivos

| Archivo | Responsabilidad |
|---------|----------------|
| `router.py` | `BrainRouter`: decide nivel, inyecta contexto, registra en `brain_reasoning` |
| `ml_engine.py` | Carga modelos .pkl de `ml/models/`, predice con confianza, feature engineering |
| `local_llm.py` | Cliente HTTP OpenAI-compatible (`/chat/completions`, `/models`) |
| `cloud_client.py` | Gemini 2.0 Flash + Claude Haiku con fallback automático en RateLimitError |
| `prompts.py` | `build_prompt(task_type, input_data)` centralizado |
| `tasks/` | Una clase por tarea: prepara features ML + prompt LLM |

## Reglas

- `BrainRouter` registra CADA decisión en tabla `brain_reasoning` (nivel, modelo, confianza, latencia_ms, tokens_used)
- `LocalLLM.is_available()` hace GET a `{base}/models` cacheado 30s — no bloquea si el servidor local está caído
- `CloudClient` captura `RateLimitError` de Gemini y hace fallback a Claude automáticamente
- Los umbrales de confianza se leen de `agent_config` en **cada llamada** → cambio en caliente sin restart
- Modelos ML están en `ml/models/` (path relativo desde raíz del proyecto)

## Salida Garantizada de BrainRouter

```python
{
    "brain_level": 1 | 2 | 3,
    "model_used": "sklearn" | "<local-model-id>" | "gemini-2.0-flash" | "claude-haiku-4-5",
    "confidence": float,   # 0.0 - 1.0
    "thought": str,        # razonamiento
    "action": str,         # acción recomendada
    "risk_level": "low" | "medium" | "high" | "critical",
    "tokens_used": int | None,
    "latency_ms": float
}
```

## Config Hot-Reload (sin restart)

Los umbrales y modos se leen de la tabla `agent_config` en cada invocación:

| Key en agent_config | Efecto |
|---------------------|--------|
| `brain.ml_confidence_threshold` | Umbral para escalar ML → Local LLM (default: 0.85) |
| `brain.local_llm_confidence_threshold` | Umbral para escalar Local LLM → Cloud (default: 0.70) |
| `brain.active_brain` | `auto` (normal) / `ml` (fuerza Nivel 1) / `local` (fuerza Nivel 2) / `cloud` (fuerza Nivel 3) |

Modificar con: `UPDATE agent_config SET value = '0.75' WHERE key = 'brain.ml_confidence_threshold';`
El cambio aplica en la **siguiente llamada** a `BrainRouter.route()`.

## Auditoría — Tabla brain_reasoning

Cada decisión queda registrada con:
- `brain_level`, `model_used`, `task_type`
- `confidence`, `latency_ms`, `tokens_used`
- `input_data` (JSONB), `output_data` (JSONB), `reasoning_text`
- `scan_id`, `finding_id` para trazabilidad completa

Consultar con: `/hunter-brain` o `/hunter-stats`
