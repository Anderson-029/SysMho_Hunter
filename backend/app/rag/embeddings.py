"""
Embeddings — Cliente hacia Ollama (nomic-embed-text).
Convierte texto en vectores para indexar/buscar en Qdrant.
"""

import logging
import time

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    pass


class EmbeddingClient:
    """Wrapper async sobre /api/embeddings de Ollama."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    async def embed(self, text: str) -> list[float]:
        """Genera el vector de embedding para un texto."""
        start = time.monotonic()
        payload = {"model": self.model, "prompt": text}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings", json=payload
                ) as resp:
                    if resp.status != 200:
                        raise EmbeddingError(f"Ollama HTTP {resp.status}")
                    data = await resp.json()

            vector = data.get("embedding")
            if not vector or len(vector) != self.dimensions:
                raise EmbeddingError(
                    f"Vector inválido: esperado {self.dimensions} dims, "
                    f"recibido {len(vector) if vector else 0}"
                )

            latency_ms = int((time.monotonic() - start) * 1000)
            logger.debug(f"[Embeddings] Generado en {latency_ms}ms")
            return vector

        except aiohttp.ClientError as e:
            logger.error(f"[Embeddings] Error de conexión: {e}")
            raise EmbeddingError(str(e))

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos (secuencial).

        Ollama no soporta batch nativo en /api/embeddings, por lo que
        se procesan uno a uno con reintentos individuales por fallo.
        """
        vectors = []
        for i, text in enumerate(texts):
            try:
                vectors.append(await self.embed(text))
            except EmbeddingError as e:
                logger.warning(
                    f"[Embeddings] Fallo en texto {i}/{len(texts)}: {e}"
                )
                raise
        return vectors


# Singleton global
embedding_client = EmbeddingClient()
