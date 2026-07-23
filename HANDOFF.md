# HANDOFF — SysMho Hunter (Fase "Esteroides RAG")

> Documento de continuidad para la próxima conversación con Claude Code.
> Última sesión: 22 Julio 2026.

---

## Contexto: Por qué existe esta fase

Anderson compartió un plan de ChatGPT/Cursor para reconstruir SysMho Hunter
desde cero como un "AI Security Research Assistant" con Next.js, Qdrant,
Neo4j, agentes especializados, MCP servers, etc.

**Decisión tomada (no reconstruir):** SysMho Hunter ya tiene la parte
operacional sólida (19 tools, scope enforcement, pending_actions, cerebro
híbrido funcionando, tests). Reconstruir desde cero perdería 2-3 meses
reimplementando lo que ya funciona. En cambio: **evolucionar el proyecto
existente inyectándole las piezas de inteligencia que le faltan** (RAG,
Neo4j, agentes) sin tocar lo que ya está validado.

Ver conversación completa para el análisis crítico detallado de qué
tomar del plan original y qué descartar (ej. modelos Ornith/LFM2.5
descartados, Qwen 3.5 9B recomendado para más adelante, Next.js descartado
por ahora).

---

## Roadmap acordado (por fases)

```
Fase 1.1: RAG Core (Qdrant + embeddings + integración cerebro)   ✅ HECHO
Fase 1.2: Poblar knowledge base (scraper PortSwigger + findings) ⏳ SIGUIENTE
Fase 2:   Neo4j (knowledge graph de relaciones entre vulns)      ⏳ pendiente
Fase 3:   Cambio LLM a Qwen 3.5 9B + fine-tuning + agentes       ⏳ pendiente
```

**Regla de oro acordada con Anderson:** cualquier comando crítico (Docker,
instalación de deps, cambios en `.env`, servicios nuevos) se reporta ANTES
de ejecutar y se espera confirmación explícita. No asumir autorización
implícita de una fase a otra.

---

## Qué se hizo en esta sesión (Fase 1.1 — completa)

### Infraestructura nueva
- `docker-compose.yml` (raíz) — servicio `qdrant` (imagen `qdrant/qdrant`,
  puertos 6333/6334, volumen persistente `qdrant_data`)
- Usuario `anderson` agregado al grupo `docker` (antes no podía correr
  Docker sin sudo — esto ya quedó resuelto a nivel de sistema)
- Qdrant corriendo, colección `security_knowledge` creada (768 dims,
  distancia coseno)
- Modelo `nomic-embed-text` descargado vía Ollama (274MB, embeddings 768d)
- BD de tests `sysmho_hunter_test` creada (no existía, bloqueaba
  `pytest` — resuelto de paso, no relacionado con RAG)

### Código nuevo
```
backend/app/rag/
├── __init__.py
├── qdrant_client.py   # QdrantStore: ensure_collection, upsert_document, search, count
├── embeddings.py      # EmbeddingClient: embed(), embed_batch() vía Ollama
├── indexer.py         # Parser Markdown+frontmatter, chunking por sección ##, index_directory()
└── retriever.py       # retrieve(query) + format_context() — usado por BrainRouter

knowledge/
├── portswigger/idor.md      # Documento de prueba (6 chunks indexados, validado)
└── labs_findings/           # Vacío, para findings de labs futuros

scripts/ingest_knowledge.py  # CLI: uv run python ../scripts/ingest_knowledge.py [dir]
```

### Código modificado
- `backend/app/config.py` — agregado `qdrant_url`, `qdrant_collection`,
  `embedding_model`, `embedding_dimensions` a `Settings`
- `backend/app/brain/prompts.py` — `build_reason_prompt()` y
  `build_report_prompt()` ahora aceptan `rag_context: str = ""`.
  Nueva función pública `rag_block(rag_context)` que formatea el bloque
  de contexto (o `""` si no hay contexto)
- `backend/app/brain/router.py` —
  - `_fetch_rag_context(task_type, input_data)`: consulta RAG,
    **try/except Exception amplio deliberado** — si Qdrant/embeddings
    fallan, retorna `""` y el cerebro sigue funcionando normal
  - `_build_rag_query(task_type, input_data)`: deriva el texto de
    búsqueda según la tarea
  - `_build_prompt()` ahora recibe `rag_context` y lo propaga
  - Se llama `_fetch_rag_context` una sola vez antes de intentar
    Nivel 2, y el resultado se reusa si escala a Nivel 3
- `backend/.env` y `backend/.env.example` — nuevas vars documentadas
- `.md` del proyecto actualizados: `CLAUDE.md`, `AGENTS.md`,
  `backend/AGENTS.md`, `backend/app/brain/AGENTS.md`, `PENDIENTES.md`

### Validación hecha
- Pipeline end-to-end probado: indexé `idor.md` → 6 chunks → query en
  lenguaje natural ("¿cómo puedo probar si un endpoint es vulnerable a
  acceso no autorizado por ID?") → devolvió los 3 fragmentos correctos
  con scores 0.70-0.77
- `BrainRouter.route("detect_patterns", {...})` con una descripción de
  IDOR real → confirmé en logs que `[Retriever]` se invocó, Ollama
  (Nivel 2) respondió `vuln_type: idor, confidence: 0.9`
- `uv run ruff check` — sin errores en archivos nuevos/modificados
- `uv run pytest ../tests/test_brain/ -v` — **12/12 passed**, sin
  regresiones tras integrar RAG

---

## Decisiones de diseño tomadas (para no repreguntar)

| Decisión | Elegido | Razón |
|---|---|---|
| Deploy Qdrant | Docker local | Aislado, fácil levantar/parar, no "todo local" roto |
| Modelo embeddings | `nomic-embed-text` (Ollama) | Ya está en el stack Ollama, no rompe "todo local" |
| Primer contenido knowledge base | PortSwigger + findings de labs (devil) | Aprobado por Anderson explícitamente |
| Cambio de LLM (Llama→Qwen) | Después de validar RAG | Aislar variables, más fácil debug |
| RAG debe ser bloqueante o best-effort | **Best-effort** | Si Qdrant cae, el cerebro no debe romperse — es una mejora, no una dependencia dura |

---

## Pendiente inmediato (Fase 1.2 — siguiente sesión)

1. **Scraper de PortSwigger Web Security Academy**
   - ⚠️ Restricción acordada: rate-limiting agresivo (1 req/3-5s), NO
     copiar texto literal completo (resumir/estructurar), uso estrictamente
     personal — PortSwigger prohíbe scraping automatizado + republicación
     en sus ToS. Si Anderson prefiere evitar el riesgo, la alternativa es
     curación manual de 10-15 técnicas clave.
   - Output esperado: un `.md` por técnica en `knowledge/portswigger/`,
     mismo formato frontmatter que `idor.md` (source, category, cwe,
     severity, url + secciones `## Descripción`, `## Cómo detectar`,
     `## Payloads`, `## Impacto`, `## Mitigación`)

2. **Findings de labs → knowledge base**
   - Requiere re-ejecutar el lab `devil` (no había datos previos en BD)
   - `bash labs/devil/auto_deploy.sh` (Terminal 1) +
     `bash labs/sysmho_integration.sh auto devil <IP> 80` (Terminal 2)
   - Estructurar los 4 findings esperados (SQLi, XSS, Auth Bypass, Info
     Disclosure) como docs en `knowledge/labs_findings/`

3. **Nice-to-have mencionados pero NO implementados aún:**
   - Endpoint REST `/api/v1/rag/search` (para probar desde Swagger/frontend)
   - Panel visual en el dashboard mostrando de dónde sale cada respuesta
     del cerebro (actualmente el RAG solo se ve por logs/consola)

---

## Cómo verificar que todo sigue funcionando al retomar

```bash
# 1. Qdrant vivo
docker ps | grep qdrant
curl http://localhost:6333/healthz

# 2. Ollama vivo + modelo de embeddings presente
curl http://localhost:11434/api/tags | grep nomic

# 3. Colección con datos
curl http://localhost:6333/collections/security_knowledge | python3 -m json.tool

# 4. Test rápido del RAG
cd backend && uv run python -c "
import asyncio
from app.rag.retriever import retrieve, format_context
async def main():
    r = await retrieve('¿cómo detecto un IDOR?', limit=3)
    print(format_context(r))
asyncio.run(main())
"

# 5. Tests del cerebro (requiere BD sysmho_hunter_test, ya creada)
uv run pytest ../tests/test_brain/ -v
```

---

## Notas de seguridad de esta sesión (para no repetir)

- El usuario compartió su contraseña de `sudo` en el chat en texto plano
  — **no la usé**, le pedí que ejecutara el comando él mismo. Se le
  recomendó rotarla.
- `backend/.env` tiene `GEMINI_API_KEY` en texto plano (correcto, está
  gitignored) pero también quedó expuesta en el chat en algún momento —
  recomendado rotarla cuando Anderson tenga oportunidad.
- Regla de trabajo confirmada por Anderson: reportar comandos/acciones
  críticas ANTES de ejecutar, permitir confirmación explícita, y poder
  preguntar para decisiones de diseño (usar `AskUserQuestion`).
