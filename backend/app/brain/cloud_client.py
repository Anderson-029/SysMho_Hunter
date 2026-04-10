"""
CloudClient — Nivel 3 del cerebro híbrido.
Primario: Gemini 2.0 Flash
Fallback: Claude Haiku
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
        self._anthropic = None

    def _get_gemini(self):
        if self._gemini is None:
            if not settings.gemini_api_key or "tu_" in settings.gemini_api_key:
                raise CloudClientError("GEMINI_API_KEY no configurada")
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            self._gemini = client
        return self._gemini

    def _get_anthropic(self):
        if self._anthropic is None:
            if (
                not settings.anthropic_api_key
                or "tu_" in settings.anthropic_api_key
            ):
                raise CloudClientError("ANTHROPIC_API_KEY no configurada")
            import anthropic

            self._anthropic = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key
            )
        return self._anthropic

    async def complete(
        self, prompt: str, max_tokens: int = 1024, expect_json: bool = True
    ) -> dict:
        """Intenta Gemini primero, luego Claude como fallback."""
        try:
            return await self._gemini_complete(prompt, max_tokens, expect_json)
        except Exception as e:
            logger.warning(
                f"[CloudClient] Gemini falló: {e}. Usando Claude fallback."
            )
            return await self._claude_complete(prompt, max_tokens, expect_json)

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
                    response_mime_type="application/json"
                    if expect_json
                    else "text/plain",
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

    async def _claude_complete(
        self, prompt: str, max_tokens: int, expect_json: bool
    ) -> dict:
        start = time.monotonic()
        client = self._get_anthropic()

        system = (
            "You are SysMho Hunter, an expert pentesting AI agent."
            " Always respond with valid JSON when asked."
        )
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        latency_ms = int((time.monotonic() - start) * 1000)

        result = self._parse_response(text, expect_json)
        result["_meta"] = {
            "model": "claude-haiku-4-5-20251001",
            "latency_ms": latency_ms,
        }
        return result

    def _parse_response(self, text: str, expect_json: bool) -> dict:
        if not expect_json:
            return {"text": text, "confidence": 0.9}
        clean = text.strip()
        # Remover bloques de código markdown
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.MULTILINE)
        clean = re.sub(r"```\s*$", "", clean, flags=re.MULTILINE).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            # Último intento: extraer JSON con regex
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise CloudClientError(
                f"Respuesta no es JSON válido: {clean[:200]}"
            )


# Singleton global
cloud_client = CloudClient()
