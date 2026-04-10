"""
MLEngine — Nivel 1 del cerebro híbrido.
Carga los modelos scikit-learn entrenados y realiza predicciones.
"""

import logging
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent.parent / "ml" / "models"

SEVERITIES = ["critical", "high", "medium", "low", "informational"]
VULN_TYPES = [
    "xss",
    "sqli",
    "ssrf",
    "rce",
    "idor",
    "lfi",
    "xxe",
    "ssti",
    "open_redirect",
    "other",
]


class MLEngine:
    """Predicciones rápidas (<10ms) con modelos scikit-learn locales."""

    def __init__(self):
        self._severity_clf = None
        self._vuln_scorer = None
        self._pattern_clf = None
        self._prioritizer = None
        self._loaded = False

    def load(self) -> bool:
        """Carga los modelos en memoria. Retorna True si todos cargaron."""
        try:
            import joblib

            self._severity_clf = joblib.load(
                MODELS_DIR / "severity_classifier.pkl"
            )
            self._vuln_scorer = joblib.load(MODELS_DIR / "vuln_scorer.pkl")
            self._pattern_clf = joblib.load(
                MODELS_DIR / "pattern_detector.pkl"
            )
            self._prioritizer = joblib.load(
                MODELS_DIR / "target_prioritizer.pkl"
            )
            self._loaded = True
            logger.info("[MLEngine] Modelos cargados correctamente.")
            return True
        except Exception as e:
            logger.warning(f"[MLEngine] No se pudieron cargar modelos: {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self._loaded

    def classify_severity(self, description: str) -> dict:
        """
        Clasifica severidad de un finding a partir de su descripción.
        Retorna: {severity, confidence, all_probs}
        """
        if not self._loaded:
            return {"severity": None, "confidence": 0.0}

        start = time.monotonic()
        probs = self._severity_clf.predict_proba([description])[0]
        classes = self._severity_clf.classes_
        best_idx = int(np.argmax(probs))
        latency = int((time.monotonic() - start) * 1000)

        return {
            "severity": classes[best_idx],
            "confidence": float(probs[best_idx]),
            "all_probs": {c: float(p) for c, p in zip(classes, probs)},
            "latency_ms": latency,
        }

    def score_vulnerability(self, description: str) -> dict:
        """
        Predice el score CVSS (0-10) de una vulnerabilidad.
        Retorna: {cvss_score, confidence}
        """
        if not self._loaded:
            return {"cvss_score": None, "confidence": 0.0}

        start = time.monotonic()
        vectorizer = self._vuln_scorer["vectorizer"]
        model = self._vuln_scorer["model"]
        X = vectorizer.transform([description]).toarray()
        score = float(model.predict(X)[0])
        score = max(0.0, min(10.0, round(score, 1)))
        latency = int((time.monotonic() - start) * 1000)

        # La confianza del scorer se estima por distancia al rango extremo
        confidence = 1.0 - (abs(score - 5.0) / 10.0)

        return {
            "cvss_score": score,
            "confidence": round(confidence, 4),
            "latency_ms": latency,
        }

    def detect_pattern(self, description: str) -> dict:
        """
        Detecta el tipo de vulnerabilidad (XSS, SQLi, SSRF, etc.)
        Retorna: {vuln_type, confidence}
        """
        if not self._loaded:
            return {"vuln_type": None, "confidence": 0.0}

        start = time.monotonic()
        probs = self._pattern_clf.predict_proba([description])[0]
        classes = self._pattern_clf.classes_
        best_idx = int(np.argmax(probs))
        latency = int((time.monotonic() - start) * 1000)

        return {
            "vuln_type": classes[best_idx],
            "confidence": float(probs[best_idx]),
            "all_probs": {c: float(p) for c, p in zip(classes, probs)},
            "latency_ms": latency,
        }

    def prioritize_target(self, features: dict) -> dict:
        """
        Predice la prioridad (1-5) de un target.
        features: {has_auth, num_endpoints, has_api, has_db,
                   tech_count, h1_submissions}
        """
        if not self._loaded:
            return {"priority": 3, "confidence": 0.0}

        start = time.monotonic()
        X = np.array(
            [
                [
                    features.get("has_auth", 0),
                    features.get("num_endpoints", 0),
                    features.get("has_api", 0),
                    features.get("has_db", 0),
                    features.get("tech_count", 0),
                    features.get("h1_submissions", 0),
                ]
            ],
            dtype=float,
        )

        probs = self._prioritizer.predict_proba(X)[0]
        classes = self._prioritizer.classes_
        best_idx = int(np.argmax(probs))
        latency = int((time.monotonic() - start) * 1000)

        return {
            "priority": int(classes[best_idx]),
            "confidence": float(probs[best_idx]),
            "latency_ms": latency,
        }


# Singleton global (cargado en lifespan de FastAPI)
ml_engine = MLEngine()
