"""
LocalLLM — Nivel 2 del cerebro híbrido.
Cliente HTTP hacia cualquier servidor OpenAI-compatible
(LM Studio, Ollama /v1, vLLM, etc.).
"""

import json
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_availability_cache: dict = {"available": None, "checked_at": 0.0}
CACHE_TTL = 30.0  # segundos


class LocalLLMError(Exception):
    pass


class LocalLLM:
    """Wrapper async sobre chat/completions OpenAI-compatible."""

    def __init__(self):
        self.base_url = settings.local_llm_base_url.rstrip("/")
        self.model = settings.local_llm_model
        self.api_key = settings.local_llm_api_key

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def is_available(self) -> bool:
        """Verifica si el servidor local responde. Cacheado 30s."""
        now = time.monotonic()
        if (
            now - _availability_cache["checked_at"]
        ) < CACHE_TTL and _availability_cache["available"] is not None:
            return _availability_cache["available"]

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                available = resp.status_code == 200
                _availability_cache["available"] = available
                _availability_cache["checked_at"] = now
                return available
        except Exception:
            _availability_cache["available"] = False
            _availability_cache["checked_at"] = now
            return False

    async def complete(self, prompt: str, max_tokens: int = 512) -> dict:
        """
        Envía prompt al LLM local y retorna respuesta parseada como dict.
        Pide JSON vía response_format; si el servidor no lo soporta,
        reintenta sin ese campo y parsea el texto.
        """
        start = time.monotonic()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a security analysis assistant. "
                    "Always respond with a single valid JSON object only."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stream": False,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                # Algunos servidores (LM Studio antiguo) no soportan
                # response_format — reintentar sin él.
                if resp.status_code in (400, 422):
                    payload.pop("response_format", None)
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=payload,
                    )
                if resp.status_code != 200:
                    raise LocalLLMError(
                        f"Local LLM HTTP {resp.status_code}: {resp.text[:200]}"
                    )
                data = resp.json()

            choices = data.get("choices") or []
            if not choices:
                raise LocalLLMError("Respuesta sin choices")
            raw_text = (
                choices[0].get("message", {}).get("content") or ""
            ).strip()
            latency_ms = int((time.monotonic() - start) * 1000)

            clean = raw_text
            if clean.startswith("```"):
                parts = clean.split("```")
                clean = parts[1] if len(parts) > 1 else clean
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            result = json.loads(clean)
            usage = data.get("usage") or {}
            result["_meta"] = {
                "model": self.model,
                "latency_ms": latency_ms,
                "tokens": usage.get("total_tokens", 0),
            }
            return result

        except json.JSONDecodeError as e:
            logger.warning("[LocalLLM] JSON inválido en respuesta: %s", e)
            raise LocalLLMError(f"Respuesta no es JSON válido: {e}") from e
        except LocalLLMError:
            raise
        except Exception as e:
            logger.error("[LocalLLM] Error: %s", e)
            raise LocalLLMError(str(e)) from e


# Singleton global
local_llm = LocalLLM()
