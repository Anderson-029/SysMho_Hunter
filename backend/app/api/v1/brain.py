"""
Brain diagnostics endpoints — estado y estadísticas del cerebro híbrido.
"""

import time
from typing import Any

from fastapi import APIRouter

from app.brain.local_llm import local_llm
from app.brain.ml_engine import ml_engine

router = APIRouter(prefix="/brain", tags=["Brain"])


@router.get("/status")
async def brain_status() -> dict[str, Any]:
    """Estado actual del cerebro híbrido."""
    ollama_available = await local_llm.is_available()

    # Test latencia Ollama
    ollama_latency_ms = None
    if ollama_available:
        start = time.monotonic()
        try:
            # Simple health check
            await local_llm.is_available()
            ollama_latency_ms = int((time.monotonic() - start) * 1000)
        except Exception:
            ollama_latency_ms = None

    return {
        "status": "operational",
        "levels": {
            "level_1": {
                "name": "MLEngine (scikit-learn)",
                "available": ml_engine.is_available,
                "latency_ms": "<10",
            },
            "level_2": {
                "name": "LocalLLM (Ollama Llama 3.1 8B)",
                "available": ollama_available,
                "model": local_llm.model if ollama_available else None,
                "latency_ms": ollama_latency_ms,
            },
            "level_3": {
                "name": "CloudClient (Gemini 2.0 Flash)",
                "available": True,
                "latency_ms": "1000-3000",
            },
        },
        "recommendation": (
            "Ollama is PRIMARY — use Level 2 by default"
            if ollama_available
            else "⚠️  Ollama unavailable — fallback to Level 3 (Cloud)"
        ),
    }


@router.get("/test")
async def brain_test() -> dict[str, Any]:
    """Test cada nivel del cerebro."""
    results = {
        "timestamp": time.time(),
        "levels_tested": {},
        "recommendation": "",
    }

    # Test Nivel 1: ML
    try:
        ml_result = ml_engine.classify_severity(
            "SQL injection vulnerability in login form"
        )
        results["levels_tested"]["level_1"] = {
            "status": "✅ OK",
            "model": "sklearn",
            "result": ml_result,
        }
    except Exception as e:
        results["levels_tested"]["level_1"] = {
            "status": "❌ FAILED",
            "error": str(e),
        }

    # Test Nivel 2: Ollama
    if await local_llm.is_available():
        try:
            start = time.monotonic()
            ollama_result = await local_llm.complete(
                'Respond with JSON: {"status": "test"}'
            )
            latency = int((time.monotonic() - start) * 1000)
            results["levels_tested"]["level_2"] = {
                "status": "✅ OK",
                "model": local_llm.model,
                "latency_ms": latency,
            }
        except Exception as e:
            results["levels_tested"]["level_2"] = {
                "status": "❌ FAILED",
                "error": str(e),
            }
    else:
        results["levels_tested"]["level_2"] = {
            "status": "⚠️  UNAVAILABLE",
            "reason": "Ollama not responding",
        }

    results["recommendation"] = (
        "✅ Ollama is PRIMARY (Level 2 working)"
        if results["levels_tested"].get("level_2", {}).get("status")
        == "✅ OK"
        else "⚠️  Ollama unavailable — fallback to Cloud (Level 3)"
    )

    return results


@router.get("/stats")
async def brain_stats() -> dict[str, Any]:
    """Estadísticas de uso del cerebro (agregadas en sesión)."""
    # Nota: En producción, estas estadísticas vendrían de una BD
    # Por ahora retornamos estructura para documentar el formato

    return {
        "message": "Stats storage not yet implemented. Implementar en Fase 3.2",
        "planned_metrics": {
            "level_1_usage_pct": 0,
            "level_2_usage_pct": 0,
            "level_3_usage_pct": 0,
            "avg_latency_level_1_ms": 0,
            "avg_latency_level_2_ms": 0,
            "avg_latency_level_3_ms": 0,
            "tasks_processed": 0,
            "errors": 0,
        },
    }
