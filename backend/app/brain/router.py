"""
BrainRouter — Orquesta los 3 niveles del cerebro híbrido.
Nivel 1: MLEngine (scikit-learn, <10ms)
Nivel 2: LocalLLM (Ollama Llama 3.1 8B Q6_K, ~20-40s)
Nivel 3: CloudClient (Gemini 2.0 Flash → Claude Haiku, ~1-3s)
"""

import json
import logging
import time
from datetime import datetime, timezone

from app.brain.cloud_client import CloudClientError, cloud_client
from app.brain.local_llm import LocalLLMError, local_llm
from app.brain.ml_engine import ml_engine
from app.brain.prompts import build_reason_prompt, build_report_prompt

logger = logging.getLogger(__name__)


def _log_brain_decision(
    task_type: str,
    level: int,
    model: str,
    latency_ms: int,
    confidence: float = 0.0,
    reason: str = "",
) -> None:
    """Registra decisión del cerebro en formato JSON estructurado."""
    decision = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_type": task_type,
        "brain_level": level,
        "model_used": model,
        "latency_ms": latency_ms,
        "confidence": confidence,
        "reason": reason,
    }
    logger.info(f"[Brain Decision] {json.dumps(decision)}")

ML_CONFIDENCE_THRESHOLD = 0.85
LOCAL_CONFIDENCE_THRESHOLD = 0.70

# Tareas que el ML puede manejar directamente
ML_TASKS = {"classify_severity", "score_vuln", "prioritize_targets"}
# Tareas que siempre necesitan LLM
LLM_TASKS = {"draft_report", "analyze_response"}
# Tareas híbridas: ML primero, LLM si confianza baja
HYBRID_TASKS = {"detect_patterns", "reason_next_steps"}


class BrainRouter:
    async def route(self, task_type: str, input_data: dict) -> dict:
        """
        Enruta la tarea al nivel apropiado del cerebro.
        Retorna resultado con metadatos: brain_level, model_used, confidence.
        """
        start = time.monotonic()

        # Nivel 1: ML (tareas estructuradas)
        if task_type in ML_TASKS or task_type in HYBRID_TASKS:
            ml_result = self._try_ml(task_type, input_data)
            if (
                ml_result
                and ml_result.get("confidence", 0) >= ML_CONFIDENCE_THRESHOLD
            ):
                ml_result["brain_level"] = 1
                ml_result["model_used"] = "sklearn"
                latency_ms = int((time.monotonic() - start) * 1000)
                ml_result["total_latency_ms"] = latency_ms
                conf = ml_result["confidence"]
                _log_brain_decision(
                    task_type=task_type,
                    level=1,
                    model="sklearn",
                    latency_ms=latency_ms,
                    confidence=conf,
                    reason=(
                        f"ML confidence {conf:.3f}"
                        f" >= {ML_CONFIDENCE_THRESHOLD}"
                    ),
                )
                return ml_result

        # Nivel 2: LocalLLM (si no es tarea LLM-only y Ollama disponible)
        if task_type not in ML_TASKS:
            if await local_llm.is_available():
                try:
                    prompt = self._build_prompt(task_type, input_data)
                    llm_result = await local_llm.complete(prompt)
                    confidence = llm_result.get(
                        "confidence", LOCAL_CONFIDENCE_THRESHOLD
                    )
                    if not isinstance(confidence, float):
                        confidence = LOCAL_CONFIDENCE_THRESHOLD

                    if confidence >= LOCAL_CONFIDENCE_THRESHOLD:
                        llm_result["brain_level"] = 2
                        llm_result["model_used"] = local_llm.model
                        llm_result["confidence"] = confidence
                        total_latency = int(
                            (time.monotonic() - start) * 1000
                        )
                        llm_result["total_latency_ms"] = total_latency
                        _log_brain_decision(
                            task_type=task_type,
                            level=2,
                            model=local_llm.model,
                            latency_ms=total_latency,
                            confidence=confidence,
                            reason=(
                                f"Ollama available, confidence "
                                f"{confidence:.3f}"
                                f" >= {LOCAL_CONFIDENCE_THRESHOLD}"
                            ),
                        )
                        return llm_result
                    else:
                        _log_brain_decision(
                            task_type=task_type,
                            level=3,
                            model="cloud",
                            latency_ms=0,
                            confidence=confidence,
                            reason=(
                                f"Ollama confidence {confidence:.3f} "
                                f"< {LOCAL_CONFIDENCE_THRESHOLD}. "
                                f"Escalando a Nivel 3."
                            ),
                        )
                except LocalLLMError as e:
                    logger.warning(
                        f"[Brain] Nivel 2 falló: {e}. Escalando a Nivel 3."
                    )
                    _log_brain_decision(
                        task_type=task_type,
                        level=3,
                        model="cloud",
                        latency_ms=0,
                        reason=f"Nivel 2 error: {str(e)}",
                    )
            else:
                _log_brain_decision(
                    task_type=task_type,
                    level=3,
                    model="cloud",
                    latency_ms=0,
                    reason="Ollama no disponible. Escalando a Nivel 3.",
                )

        # Nivel 3: Cloud (siempre disponible como último recurso)
        try:
            prompt = self._build_prompt(task_type, input_data)
            expect_json = task_type != "draft_report"
            cloud_result = await cloud_client.complete(
                prompt, expect_json=expect_json
            )
            cloud_result["brain_level"] = 3
            model_name = cloud_result.get("_meta", {}).get(
                "model", "cloud"
            )
            cloud_result["model_used"] = model_name
            cloud_result["confidence"] = cloud_result.get("confidence", 0.9)
            total_latency = int((time.monotonic() - start) * 1000)
            cloud_result["total_latency_ms"] = total_latency
            _log_brain_decision(
                task_type=task_type,
                level=3,
                model=model_name,
                latency_ms=total_latency,
                confidence=cloud_result.get("confidence", 0.9),
                reason="Cloud fallback (Nivel 1 y 2 no disponibles)",
            )
            return cloud_result
        except CloudClientError as e:
            logger.error(f"[Brain] Todos los niveles fallaron: {e}")
            _log_brain_decision(
                task_type=task_type,
                level=0,
                model="none",
                latency_ms=int((time.monotonic() - start) * 1000),
                reason=f"CRITICAL ERROR: todos los niveles fallaron: {str(e)}",
            )
            return {
                "error": str(e),
                "brain_level": 0,
                "model_used": "none",
                "confidence": 0.0,
                "thought": "Error en todos los cerebros disponibles.",
                "action": "standard_scan",
                "command_suggestion": "manual_review",
                "priority": "medium",
                "risk_level": "low",
            }

    def _try_ml(self, task_type: str, input_data: dict) -> dict | None:
        """Intenta resolver la tarea con ML. Retorna None si no aplica."""
        if not ml_engine.is_available:
            return None

        description = input_data.get("description", input_data.get("text", ""))

        if task_type == "classify_severity":
            return ml_engine.classify_severity(description)
        elif task_type == "score_vuln":
            return ml_engine.score_vulnerability(description)
        elif task_type == "prioritize_targets":
            return ml_engine.prioritize_target(input_data)
        elif task_type == "detect_patterns":
            return ml_engine.detect_pattern(description)
        elif task_type == "reason_next_steps":
            # ML detecta patrón principal; LLM si confianza baja
            pattern_result = ml_engine.detect_pattern(description)
            vtype = pattern_result["vuln_type"]
            if pattern_result.get("confidence", 0) >= ML_CONFIDENCE_THRESHOLD:
                return {
                    "thought": (
                        f"ML detectó patrón: {vtype} con alta confianza"
                    ),
                    "action": f"{vtype}_test",
                    "command_suggestion": f"Test específico para {vtype}",
                    "priority": "high",
                    "risk_level": "medium",
                    "confidence": pattern_result["confidence"],
                }
        return None

    def _build_prompt(self, task_type: str, input_data: dict) -> str:
        """Construye el prompt para LLM según el tipo de tarea."""
        if task_type == "reason_next_steps":
            return build_reason_prompt(
                target_url=input_data.get("target_url", ""),
                recon_data=input_data.get("recon_data", {}),
                findings=input_data.get("findings", []),
            )
        elif task_type == "draft_report":
            return build_report_prompt(
                target=input_data.get("target", ""),
                finding=input_data.get("finding", {}),
            )
        elif task_type == "analyze_response":
            body = str(input_data.get("body", ""))[:2000]
            return (
                "Analyze this HTTP response for security vulnerabilities.\n"
                f"Target: {input_data.get('url', '')}\n"
                f"Response Status: {input_data.get('status_code', '')}\n"
                f"Response Headers: {input_data.get('headers', {})}\n"
                f"Response Body (first 2000 chars): {body}\n\n"
                'Respond with JSON: {"vulnerabilities": [...],'
                ' "risk_assessment": "...", "confidence": 0.0-1.0}'
            )
        elif task_type == "detect_patterns":
            desc = input_data.get("description", "")
            return (
                f"Detect vulnerability patterns in this text: {desc}\n"
                'Respond with JSON: {"vuln_type":'
                ' "xss|sqli|ssrf|rce|idor|lfi|other",'
                ' "confidence": 0.0-1.0, "reasoning": "..."}'
            )
        else:
            return (
                f"Task: {task_type}\n"
                f"Input: {input_data}\n"
                "Respond with JSON."
            )


# Singleton global
brain_router = BrainRouter()
