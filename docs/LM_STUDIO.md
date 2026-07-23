# docs/LM_STUDIO.md — LLM local OpenAI-compatible (LM Studio y similares)

SysMho Hunter **no depende de Ollama**. El Nivel 2 del cerebro y los
embeddings RAG hablan con cualquier servidor **OpenAI-compatible**.

## LM Studio (recomendado en macOS)

1. Instala [LM Studio](https://lmstudio.ai/).
2. Descarga un modelo de chat (p. ej. Qwen / Llama instruct).
3. Descarga un modelo de embeddings (p. ej. nomic-embed-text) si usas RAG.
4. Abre **Local Server** (Developer → Local Server) y arranca el servidor.
   - URL típica: `http://localhost:1234/v1`
5. En `backend/.env`:

```env
LOCAL_LLM_BASE_URL=http://localhost:1234/v1
LOCAL_LLM_MODEL=<id exacto del modelo de chat en LM Studio>
LOCAL_LLM_API_KEY=lm-studio
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=<id exacto del modelo de embeddings>
EMBEDDING_DIMENSIONS=768
```

6. Verifica:

```bash
curl -s http://localhost:1234/v1/models \
  -H "Authorization: Bearer lm-studio"
bash scripts/doctor.sh
```

## Ollama (opcional, modo OpenAI)

Si prefieres Ollama, usa la API compatible:

```env
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.1:8b-instruct-q6_K
EMBEDDING_MODEL=nomic-embed-text
```

No uses endpoints nativos `/api/generate` ni `/api/tags` — el código ya no
los llama.

## Notas

- Si cambias `EMBEDDING_DIMENSIONS`, reindexa Qdrant (`ingest_knowledge.py`).
- Sin Local LLM ni `GEMINI_API_KEY`, el cerebro degrada (Nivel 1 ML si hay
  `.pkl`, si no `brain_level=0`).
