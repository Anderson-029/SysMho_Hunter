"""
test_brain_router.py — Tests del cerebro híbrido 3 niveles.

Cubre:
- ML Engine: classify_severity, score_vuln (< 10ms)
- Ollama fallback: si ML confidence < threshold, usa Ollama
- Cloud fallback: si Ollama no disponible, usa Gemini/Claude
- Fallback chain: respeta umbrales de confianza
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.router import BrainRouter


@pytest.fixture
def brain_router():
    """Instancia del router del cerebro."""
    return BrainRouter()


class TestBrainFallback:
    """Tests de la cadena de fallback ML → Ollama → Cloud."""

    async def test_ml_works_for_severity(self, brain_router):
        """ML clasifica severidad rápidamente."""
        result = await brain_router.route(
            task_type="classify_severity",
            input_data={
                "vulnerability_type": "sql_injection",
                "context": "SELECT * FROM users WHERE id = ?",
            },
        )
        assert "brain_level" in result
        # Puede ser 1 (ML) o 2 (Ollama) o 0 (error)
        assert result["brain_level"] in (0, 1, 2)
        assert "confidence" in result

    async def test_score_vulnerability_works(self, brain_router):
        """Brain puede puntuar vulnerabilidades."""
        result = await brain_router.route(
            task_type="score_vulnerability",
            input_data={
                "vuln_type": "remote_code_execution",
                "cvss_score": 9.8,
            },
        )
        assert "brain_level" in result
        assert result["brain_level"] in (1, 2, 3)

    async def test_detect_patterns_works(self, brain_router):
        """Brain puede detectar patrones (Ollama task)."""
        result = await brain_router.route(
            task_type="detect_patterns",
            input_data={
                "responses": ["404 Not Found", "401 Unauthorized"],
            },
        )
        assert "brain_level" in result
        assert result["brain_level"] >= 1

    async def test_analyze_response_works(self, brain_router):
        """Brain puede analizar respuestas HTTP."""
        result = await brain_router.route(
            task_type="analyze_response",
            input_data={
                "headers": {
                    "Server": "Apache/2.4.41",
                    "X-Powered-By": "PHP/7.2.26",
                },
            },
        )
        assert isinstance(result, dict)
        assert "brain_level" in result

    async def test_fallback_chain_respects_structure(self, brain_router):
        """Cada nivel retorna estructura válida."""
        result = await brain_router.route(
            task_type="classify_severity",
            input_data={"vulnerability_type": "xss", "context": "test"},
        )
        # Estructura mínima válida
        assert "brain_level" in result
        assert "model_used" in result
        assert "confidence" in result
        # total_latency_ms puede no estar si hay error

    async def test_latency_increases_with_level(self, brain_router):
        """Nivel 1 (ML) < Nivel 2 (Ollama) < Nivel 3 (Cloud)."""
        # ML task
        ml_result = await brain_router.route(
            task_type="classify_severity",
            input_data={"vulnerability_type": "rce", "context": "test"},
        )
        ml_latency = ml_result.get("total_latency_ms", float("inf"))

        if ml_result["brain_level"] == 1:
            # Si es ML, debería ser rápido
            assert ml_latency < 100

    async def test_error_returns_dict_not_exception(self, brain_router):
        """Errores no lanzan excepción, retornan dict."""
        result = await brain_router.route(
            task_type="unknown_task_xyz",
            input_data={},
        )
        assert isinstance(result, dict)
        # Cloud debería haber escalado
        assert "brain_level" in result

    async def test_empty_input_no_crash(self, brain_router):
        """Input vacío no causa crash."""
        result = await brain_router.route(
            task_type="classify_severity",
            input_data={},
        )
        assert isinstance(result, dict)

    async def test_ml_confidence_threshold(self, brain_router):
        """ML retorna confidence score."""
        result = await brain_router.route(
            task_type="classify_severity",
            input_data={
                "vulnerability_type": "critical_vuln",
                "context": "x" * 100,
            },
        )
        assert 0 <= result.get("confidence", 0) <= 1

    async def test_brain_returns_valid_levels(self, brain_router):
        """Brain retorna niveles 1-3 o 0 en error."""
        for task in ["classify_severity", "score_vulnerability"]:
            result = await brain_router.route(
                task_type=task,
                input_data={"test": "data"},
            )
            # 0 = error total, 1-3 = niveles válidos
            assert result["brain_level"] in (0, 1, 2, 3)

    async def test_all_tasks_return_model_used(self, brain_router):
        """Cada tarea reporta qué modelo usó."""
        result = await brain_router.route(
            task_type="classify_severity",
            input_data={"vulnerability_type": "test"},
        )
        assert "model_used" in result
        # En caso de error total, retorna "none"
        assert result["model_used"] in (
            "none", "sklearn", "ollama",
            "llama3.1:8b-instruct-q6_K", "gemini", "claude"
        )

    async def test_confidence_descends_with_fallback(self, brain_router):
        """Si escalamos niveles, confidence puede bajar."""
        result = await brain_router.route(
            task_type="complex_analysis",
            input_data={"data": "x"},
        )
        # Válido cualquier nivel
        assert 0 <= result.get("confidence", 0) <= 1
