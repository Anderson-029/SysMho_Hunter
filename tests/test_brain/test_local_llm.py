"""
Tests unitarios LocalLLM + EmbeddingClient (API OpenAI-compatible).
No requieren LM Studio ni Ollama reales.
"""

import json

import httpx
import pytest

from app.brain.local_llm import LocalLLM, LocalLLMError, _availability_cache
from app.rag.embeddings import EmbeddingClient, EmbeddingError

_RealAsyncClient = httpx.AsyncClient


def _reset_availability_cache() -> None:
    _availability_cache["available"] = None
    _availability_cache["checked_at"] = 0.0


def _patch_async_client(monkeypatch, transport: httpx.MockTransport) -> None:
    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        kwargs.pop("timeout", None)
        return _RealAsyncClient(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


@pytest.fixture
def local_llm() -> LocalLLM:
    _reset_availability_cache()
    llm = LocalLLM()
    llm.base_url = "http://llm.test/v1"
    llm.model = "test-model"
    llm.api_key = "test-key"
    return llm


@pytest.fixture
def embedding_client() -> EmbeddingClient:
    client = EmbeddingClient()
    client.base_url = "http://llm.test/v1"
    client.model = "test-embed"
    client.dimensions = 3
    client.api_key = "test-key"
    return client


class TestLocalLLM:
    async def test_is_available_ok(self, local_llm, monkeypatch):
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/models"
            return httpx.Response(200, json={"data": [{"id": "test-model"}]})

        _patch_async_client(monkeypatch, httpx.MockTransport(handler))
        assert await local_llm.is_available() is True

    async def test_is_available_down(self, local_llm, monkeypatch):
        class Boom:
            async def __aenter__(self):
                raise httpx.ConnectError("down")

            async def __aexit__(self, *args):
                return False

        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: Boom())
        assert await local_llm.is_available() is False

    async def test_complete_parses_json(self, local_llm, monkeypatch):
        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"status": "ok", "confidence": 0.9}
                        )
                    }
                }
            ],
            "usage": {"total_tokens": 12},
        }

        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/chat/completions"
            return httpx.Response(200, json=body)

        _patch_async_client(monkeypatch, httpx.MockTransport(handler))
        result = await local_llm.complete('Respond JSON: {"status":"ok"}')
        assert result["status"] == "ok"
        assert result["_meta"]["tokens"] == 12
        assert result["_meta"]["model"] == "test-model"

    async def test_complete_invalid_json_raises(self, local_llm, monkeypatch):
        body = {
            "choices": [{"message": {"content": "not-json"}}],
            "usage": {},
        }

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=body)

        _patch_async_client(monkeypatch, httpx.MockTransport(handler))
        with pytest.raises(LocalLLMError):
            await local_llm.complete("hi")


class TestEmbeddingClient:
    async def test_embed_ok(self, embedding_client, monkeypatch):
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/embeddings"
            return httpx.Response(
                200,
                json={"data": [{"embedding": [0.1, 0.2, 0.3]}]},
            )

        _patch_async_client(monkeypatch, httpx.MockTransport(handler))
        vec = await embedding_client.embed("hello")
        assert vec == [0.1, 0.2, 0.3]

    async def test_embed_wrong_dims(self, embedding_client, monkeypatch):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"data": [{"embedding": [1.0, 2.0]}]},
            )

        _patch_async_client(monkeypatch, httpx.MockTransport(handler))
        with pytest.raises(EmbeddingError):
            await embedding_client.embed("hello")
