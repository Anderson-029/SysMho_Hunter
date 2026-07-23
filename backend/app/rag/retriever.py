"""
Retriever — Interfaz de alto nivel para consultas RAG.
Convierte una pregunta en texto a resultados relevantes de la knowledge base.
"""

import logging

from app.rag.embeddings import embedding_client
from app.rag.qdrant_client import qdrant_store

logger = logging.getLogger(__name__)


async def retrieve(
    query: str,
    limit: int = 5,
    category: str | None = None,
    source: str | None = None,
    score_threshold: float = 0.5,
) -> list[dict]:
    """Busca documentos relevantes para una query en lenguaje natural.

    Uso típico: enriquecer el prompt del cerebro híbrido (Nivel 2/3)
    con contexto técnico real antes de generar un análisis.
    """
    vector = await embedding_client.embed(query)
    results = await qdrant_store.search(
        query_vector=vector,
        limit=limit,
        category=category,
        source=source,
        score_threshold=score_threshold,
    )
    logger.info(
        f"[Retriever] Query='{query[:50]}...' → {len(results)} resultados"
    )
    return results


def format_context(results: list[dict]) -> str:
    """Formatea resultados del RAG como bloque de contexto para un prompt."""
    if not results:
        return ""

    blocks = []
    for r in results:
        header = f"[{r['source']} | {r['category']} | score={r['score']:.2f}]"
        blocks.append(f"{header}\n{r['text']}")

    return "\n\n---\n\n".join(blocks)
