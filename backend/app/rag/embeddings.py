"""
Embeddings — Cliente OpenAI-compatible (/v1/embeddings).
Convierte texto en vectores para indexar/buscar en Qdrant.
Compatible con LM Studio, Ollama /v1, etc.
"""

import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    pass


class EmbeddingClient:
    """Wrapper async sobre POST /embeddings OpenAI-compatible."""

    def __init__(self):
        self.base_url = (
            settings.embedding_base_url or settings.local_llm_base_url
        ).rstrip("/")
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.api_key = settings.local_llm_api_key

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def embed(self, text: str) -> list[float]:
        """Genera el vector de embedding para un texto."""
        start = time.monotonic()
        payload = {"model": self.model, "input": text}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code != 200:
                    raise EmbeddingError(
                        f"Embeddings HTTP {resp.status_code}: "
                        f"{resp.text[:200]}"
                    )
                data = resp.json()

            items = data.get("data") or []
            if not items:
                raise EmbeddingError("Respuesta sin data de embeddings")
            vector = items[0].get("embedding")
            if not vector or len(vector) != self.dimensions:
                raise EmbeddingError(
                    f"Vector inválido: esperado {self.dimensions} dims, "
                    f"recibido {len(vector) if vector else 0}"
                )

            latency_ms = int((time.monotonic() - start) * 1000)
            logger.debug("[Embeddings] Generado en %sms", latency_ms)
            return vector

        except EmbeddingError:
            raise
        except httpx.HTTPError as e:
            logger.error("[Embeddings] Error de conexión: %s", e)
            raise EmbeddingError(str(e)) from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos (secuencial)."""
        vectors = []
        for i, text in enumerate(texts):
            try:
                vectors.append(await self.embed(text))
            except EmbeddingError as e:
                logger.warning(
                    "[Embeddings] Fallo en texto %s/%s: %s",
                    i,
                    len(texts),
                    e,
                )
                raise
        return vectors


# Singleton global
embedding_client = EmbeddingClient()
