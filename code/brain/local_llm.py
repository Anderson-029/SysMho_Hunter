"""
LocalLLM — Nivel 2 del cerebro híbrido.
Cliente HTTP hacia Ollama (localhost:11434).

Soporta múltiples modelos: cada agente especializado (ver agents.py) puede
pedir su propio modelo y system prompt. Si el modelo solicitado no está
instalado, degrada al modelo por defecto (estabilidad).
"""

import json
import logging
import time

import aiohttp

from config import settings

logger = logging.getLogger(__name__)

_availability_cache: dict = {"available": None, "checked_at": 0.0}
_models_cache: dict = {"models": None, "checked_at": 0.0}
CACHE_TTL = 30.0  # segundos


class LocalLLMError(Exception):
    pass


class LocalLLM:
    """Wrapper async sobre la API de Ollama (multi-modelo)."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model  # modelo por defecto / fallback

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

    async def installed_models(self) -> set[str]:
        """Set de modelos instalados en Ollama. Cacheado 30s."""
        now = time.monotonic()
        if (now - _models_cache["checked_at"]) < CACHE_TTL and _models_cache[
            "models"
        ] is not None:
            return _models_cache["models"]

        models: set[str] = set()
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=3)
            ) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for m in data.get("models", []):
                            name = m.get("name") or m.get("model", "")
                            if name:
                                models.add(name)
        except Exception as e:
            logger.warning(f"[LocalLLM] No pude listar modelos: {e}")

        _models_cache["models"] = models
        _models_cache["checked_at"] = now
        return models

    async def resolve_model(self, requested: str | None) -> str:
        """Devuelve el modelo a usar. Si el solicitado no está instalado,
        degrada al modelo por defecto (y lo registra)."""
        if not requested:
            return self.model
        installed = await self.installed_models()
        if not installed:
            # No pudimos verificar — intentamos con el solicitado igual.
            return requested
        if requested in installed:
            return requested
        logger.warning(
            f"[LocalLLM] Modelo '{requested}' no instalado. "
            f"Usando fallback '{self.model}'."
        )
        return self.model

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 512,
    ) -> dict:
        """
        Envía prompt a Ollama (/api/chat) y retorna respuesta parseada JSON.

        model:  modelo a usar (default/fallback si None o no instalado).
        system: system prompt del agente (rol especializado).
        """
        start = time.monotonic()
        use_model = await self.resolve_model(model)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": use_model,
            "messages": messages,
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
                timeout=aiohttp.ClientTimeout(total=180)
            ) as session:
                async with session.post(
                    f"{self.base_url}/api/chat", json=payload
                ) as resp:
                    if resp.status != 200:
                        raise LocalLLMError(f"Ollama HTTP {resp.status}")
                    data = await resp.json()

            raw_text = data.get("message", {}).get("content", "")
            latency_ms = int((time.monotonic() - start) * 1000)

            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]

            result = json.loads(clean)
            result["_meta"] = {
                "model": use_model,
                "latency_ms": latency_ms,
                "tokens": data.get("eval_count", 0),
            }
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"[LocalLLM] JSON inválido en respuesta: {e}")
            raise LocalLLMError(f"Respuesta no es JSON válido: {e}")
        except LocalLLMError:
            raise
        except Exception as e:
            logger.error(f"[LocalLLM] Error: {e}")
            raise LocalLLMError(str(e))


# Singleton global
local_llm = LocalLLM()
