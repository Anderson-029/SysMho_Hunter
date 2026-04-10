"""
LocalLLM — Nivel 2 del cerebro híbrido.
Cliente HTTP hacia Ollama (localhost:11434).
Soporta tool use / JSON mode de Llama 3.1 8B.
"""

import json
import logging
import time

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)

_availability_cache: dict = {"available": None, "checked_at": 0.0}
CACHE_TTL = 30.0  # segundos


class LocalLLMError(Exception):
    pass


class LocalLLM:
    """Wrapper async sobre la API de Ollama."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def is_available(self) -> bool:
        """Verifica si Ollama está corriendo. Resultado cacheado 30s."""
        now = time.monotonic()
        if (
            now - _availability_cache["checked_at"]
        ) < CACHE_TTL and _availability_cache["available"] is not None:
            return _availability_cache["available"]

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=3)
            ) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    available = resp.status == 200
                    _availability_cache["available"] = available
                    _availability_cache["checked_at"] = now
                    return available
        except Exception:
            _availability_cache["available"] = False
            _availability_cache["checked_at"] = now
            return False

    async def complete(self, prompt: str, max_tokens: int = 512) -> dict:
        """
        Envía prompt a Ollama y retorna respuesta parseada.
        Usa format=json para forzar JSON válido en la respuesta.
        """
        start = time.monotonic()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1,
                "num_thread": 8,
            },
        }

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120)
            ) as session:
                async with session.post(
                    f"{self.base_url}/api/generate", json=payload
                ) as resp:
                    if resp.status != 200:
                        raise LocalLLMError(f"Ollama HTTP {resp.status}")
                    data = await resp.json()

            raw_text = data.get("response", "")
            latency_ms = int((time.monotonic() - start) * 1000)

            # Limpiar y parsear JSON
            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]

            result = json.loads(clean)
            result["_meta"] = {
                "model": self.model,
                "latency_ms": latency_ms,
                "tokens": data.get("eval_count", 0),
            }
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"[LocalLLM] JSON inválido en respuesta: {e}")
            raise LocalLLMError(f"Respuesta no es JSON válido: {e}")
        except Exception as e:
            logger.error(f"[LocalLLM] Error: {e}")
            raise LocalLLMError(str(e))


# Singleton global
local_llm = LocalLLM()
