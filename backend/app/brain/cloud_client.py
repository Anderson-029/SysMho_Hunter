"""
CloudClient — Nivel 3 del cerebro híbrido.
Proveedor: Gemini 2.0 Flash (google-genai).
Si la cuota gratuita se agota, retorna error estructurado sin crashear.
"""

import json
import logging
import re
import time

from app.config import settings

logger = logging.getLogger(__name__)


class CloudClientError(Exception):
    pass


class CloudClient:
    def __init__(self):
        self._gemini = None

    def _get_gemini(self):
        if self._gemini is None:
            if not settings.gemini_api_key or "tu_" in settings.gemini_api_key:
                raise CloudClientError("GEMINI_API_KEY no configurada en .env")
            from google import genai

            self._gemini = genai.Client(api_key=settings.gemini_api_key)
        return self._gemini

    async def complete(
        self, prompt: str, max_tokens: int = 1024, expect_json: bool = True
    ) -> dict:
        """Llama a Gemini 2.0 Flash. Maneja errores de cuota sin crashear."""
        try:
            return await self._gemini_complete(prompt, max_tokens, expect_json)
        except CloudClientError:
            raise
        except Exception as e:
            err_str = str(e).lower()
            if any(
                k in err_str
                for k in ("quota", "rate", "429", "resource_exhausted")
            ):
                logger.warning("[CloudClient] Cuota de Gemini agotada.")
                return {
                    "thought": (
                        "Cuota de Gemini agotada. "
                        "Reintenta en unos minutos."
                    ),
                    "action": "retry_later",
                    "risk_level": "low",
                    "confidence": 0.0,
                    "brain_level": 3,
                    "model_used": "gemini-2.0-flash",
                    "_meta": {
                        "model": "gemini-2.0-flash",
                        "latency_ms": 0,
                        "quota_exceeded": True,
                    },
                }
            logger.error(f"[CloudClient] Error Gemini: {e}")
            raise CloudClientError(f"Gemini error: {e}") from e

    async def _gemini_complete(
        self, prompt: str, max_tokens: int, expect_json: bool
    ) -> dict:
        import asyncio

        start = time.monotonic()
        client = self._get_gemini()

        def _sync_call():
            from google.genai import types

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.1,
                    response_mime_type=(
                        "application/json" if expect_json else "text/plain"
                    ),
                ),
            )
            return response.text

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _sync_call)
        latency_ms = int((time.monotonic() - start) * 1000)

        result = self._parse_response(text, expect_json)
        result["_meta"] = {
            "model": "gemini-2.0-flash",
            "latency_ms": latency_ms,
        }
        return result

    def _parse_response(self, text: str, expect_json: bool) -> dict:
        if not expect_json:
            return {"text": text, "confidence": 0.9}
        clean = text.strip()
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.MULTILINE)
        clean = re.sub(r"```\s*$", "", clean, flags=re.MULTILINE).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise CloudClientError(
                f"Respuesta no es JSON válido: {clean[:200]}"
            )


# Singleton global
cloud_client = CloudClient()
