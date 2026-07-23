"""
QdrantStore — Wrapper async sobre Qdrant (vector DB local).
Gestiona la colección `security_knowledge` y operaciones CRUD de vectores.
"""

import logging
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantStore:
    """Wrapper async sobre Qdrant para la colección de conocimiento."""

    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.collection = settings.qdrant_collection
        self.dimensions = settings.embedding_dimensions

    async def ensure_collection(self) -> None:
        """Crea la colección si no existe. Idempotente."""
        exists = await self.client.collection_exists(self.collection)
        if exists:
            logger.info(f"[Qdrant] Colección '{self.collection}' ya existe")
            return

        await self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=self.dimensions, distance=Distance.COSINE
            ),
        )
        logger.info(f"[Qdrant] Colección '{self.collection}' creada")

    async def upsert_document(
        self,
        vector: list[float],
        text: str,
        source: str,
        category: str,
        metadata: dict | None = None,
        point_id: str | None = None,
    ) -> str:
        """Inserta o actualiza un documento indexado.

        Args:
            vector: embedding del texto (768 dims)
            text: contenido del chunk (para mostrar en resultados)
            source: origen (ej. "portswigger", "labs_findings")
            category: técnica/vulnerabilidad (ej. "idor", "jwt")
            metadata: campos adicionales (cwe, severity, url, etc.)
            point_id: UUID fijo para actualizar un doc existente

        Returns:
            El point_id usado (nuevo o el pasado).
        """
        pid = point_id or str(uuid.uuid4())
        payload = {
            "text": text,
            "source": source,
            "category": category,
            **(metadata or {}),
        }

        await self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(id=pid, vector=vector, payload=payload)],
        )
        return pid

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        category: str | None = None,
        source: str | None = None,
        score_threshold: float = 0.5,
    ) -> list[dict]:
        """Búsqueda semántica por similitud coseno.

        Filtros opcionales por categoría o fuente para acotar resultados.
        """
        query_filter = None
        conditions = []
        if category:
            conditions.append(
                FieldCondition(
                    key="category", match=MatchValue(value=category)
                )
            )
        if source:
            conditions.append(
                FieldCondition(key="source", match=MatchValue(value=source))
            )
        if conditions:
            query_filter = Filter(must=conditions)

        results = await self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
        )

        return [
            {
                "id": point.id,
                "score": point.score,
                "text": point.payload.get("text", ""),
                "source": point.payload.get("source", ""),
                "category": point.payload.get("category", ""),
                "metadata": {
                    k: v
                    for k, v in point.payload.items()
                    if k not in ("text", "source", "category")
                },
            }
            for point in results.points
        ]

    async def count(self) -> int:
        """Cantidad de documentos indexados en la colección."""
        info = await self.client.get_collection(self.collection)
        return info.points_count

    async def close(self) -> None:
        await self.client.close()


# Singleton global
qdrant_store = QdrantStore()
