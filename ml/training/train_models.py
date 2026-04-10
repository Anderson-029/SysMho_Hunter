"""
Script de entrenamiento de los 4 modelos ML de SysMho Hunter.
Usa datos sintéticos basados en patrones reales de CVEs/CWE para el bootstrap inicial.
Cuando se tengan datos reales (ml/data/processed/), reentrenar con esos.

Ejecutar: cd SysMho_Hunter && uv run python ml/training/train_models.py
"""
import sys
import os
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error
import joblib

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("=== SysMho Hunter — Entrenamiento de Modelos ML ===\n")

# ============================================================
# DATOS SINTÉTICOS (bootstrap inicial)
# Basados en distribuciones reales de CVEs con CVSS v3
# ============================================================

VULN_TYPES = ["xss", "sqli", "ssrf", "rce", "idor", "lfi", "xxe", "ssti", "open_redirect", "other"]
SEVERITIES = ["critical", "high", "medium", "low", "informational"]

np.random.seed(42)
N = 3000

def generate_training_data(n: int) -> tuple[list, list, list, list]:
    descriptions = []
    severities = []
    cvss_scores = []
    vuln_types = []

    templates = {
        "rce": {
            "texts": [
                "Remote code execution via deserialization vulnerability",
                "Command injection in parameter allows arbitrary code execution",
                "RCE through unsafe eval() function call",
                "Server-side template injection leading to remote code execution",
            ],
            "severity_weights": [0.7, 0.25, 0.05, 0, 0],
            "cvss_range": (8.5, 10.0),
        },
        "sqli": {
            "texts": [
                "SQL injection in login parameter allows authentication bypass",
                "Blind SQL injection in search parameter",
                "Union-based SQL injection extracts database contents",
                "Time-based SQL injection in user id parameter",
            ],
            "severity_weights": [0.2, 0.5, 0.25, 0.05, 0],
            "cvss_range": (6.5, 9.8),
        },
        "ssrf": {
            "texts": [
                "Server-side request forgery allows internal network access",
                "SSRF via URL parameter reads AWS metadata endpoint",
                "Blind SSRF through webhook URL parameter",
            ],
            "severity_weights": [0.1, 0.55, 0.3, 0.05, 0],
            "cvss_range": (5.0, 9.0),
        },
        "xss": {
            "texts": [
                "Reflected XSS in search parameter without sanitization",
                "Stored XSS in user profile field",
                "DOM-based XSS via location.hash manipulation",
                "XSS in error message allows cookie theft",
            ],
            "severity_weights": [0.05, 0.35, 0.4, 0.15, 0.05],
            "cvss_range": (3.5, 8.5),
        },
        "idor": {
            "texts": [
                "Insecure direct object reference allows accessing other users data",
                "IDOR in API endpoint exposes private user information",
                "Broken access control allows horizontal privilege escalation",
            ],
            "severity_weights": [0.1, 0.45, 0.35, 0.1, 0],
            "cvss_range": (4.0, 8.5),
        },
        "lfi": {
            "texts": [
                "Local file inclusion via path traversal in filename parameter",
                "LFI allows reading /etc/passwd and application configs",
                "Path traversal via ../ sequences in file download endpoint",
            ],
            "severity_weights": [0.15, 0.45, 0.3, 0.1, 0],
            "cvss_range": (5.0, 8.0),
        },
        "xxe": {
            "texts": [
                "XML external entity injection in SOAP endpoint",
                "XXE via file upload parsing allows reading local files",
                "Blind XXE through out-of-band data exfiltration",
            ],
            "severity_weights": [0.1, 0.5, 0.35, 0.05, 0],
            "cvss_range": (5.5, 9.0),
        },
        "ssti": {
            "texts": [
                "Server-side template injection in Jinja2 template",
                "SSTI in Twig template engine allows code execution",
                "Template injection via user-controlled input in email template",
            ],
            "severity_weights": [0.4, 0.45, 0.15, 0, 0],
            "cvss_range": (7.0, 10.0),
        },
        "open_redirect": {
            "texts": [
                "Open redirect via next parameter in login flow",
                "Unvalidated redirect allows phishing attacks",
            ],
            "severity_weights": [0, 0.1, 0.45, 0.4, 0.05],
            "cvss_range": (2.0, 5.5),
        },
        "other": {
            "texts": [
                "Information disclosure via verbose error messages",
                "Missing rate limiting on authentication endpoint",
                "Sensitive data exposed in API response",
                "Security misconfiguration in server headers",
                "Weak cryptography in session token generation",
            ],
            "severity_weights": [0.05, 0.15, 0.35, 0.35, 0.1],
            "cvss_range": (1.0, 7.0),
        },
    }

    per_type = n // len(templates)
    for vtype, tmpl in templates.items():
        for _ in range(per_type):
            text = np.random.choice(tmpl["texts"])
            # Agregar variación al texto
            variations = [" in web application", " affecting all users", " without authentication",
                         " via GET parameter", " in REST API", " reported by researcher"]
            text += np.random.choice(variations)

            sev = np.random.choice(SEVERITIES, p=tmpl["severity_weights"])
            low_cvss, high_cvss = tmpl["cvss_range"]
            cvss = round(np.random.uniform(low_cvss, high_cvss), 1)

            descriptions.append(text)
            severities.append(sev)
            cvss_scores.append(cvss)
            vuln_types.append(vtype)

    return descriptions, severities, cvss_scores, vuln_types


descriptions, severities, cvss_scores, vuln_types = generate_training_data(N)
print(f"Datos generados: {len(descriptions)} muestras")

# ============================================================
# MODELO 1: SeverityClassifier
# ============================================================
print("\n[1/4] Entrenando SeverityClassifier...")

X_train, X_test, y_train, y_test = train_test_split(descriptions, severities, test_size=0.2, random_state=42)

severity_pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
    ("clf", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)),
])
severity_pipeline.fit(X_train, y_train)
y_pred = severity_pipeline.predict(X_test)
acc = (np.array(y_pred) == np.array(y_test)).mean()
print(f"  Accuracy: {acc:.3f}")
print(f"  {classification_report(y_test, y_pred, zero_division=0)}")

joblib.dump(severity_pipeline, MODELS_DIR / "severity_classifier.pkl")
print(f"  Guardado: {MODELS_DIR}/severity_classifier.pkl")

# ============================================================
# MODELO 2: VulnScorer (regresión CVSS)
# ============================================================
print("\n[2/4] Entrenando VulnScorer...")

vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
X_vec = vectorizer.fit_transform(descriptions).toarray()

X_train, X_test, y_train, y_test = train_test_split(X_vec, cvss_scores, test_size=0.2, random_state=42)

scorer = GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, random_state=42)
scorer.fit(X_train, y_train)
y_pred = scorer.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"  RMSE: {rmse:.3f}")

joblib.dump({"vectorizer": vectorizer, "model": scorer}, MODELS_DIR / "vuln_scorer.pkl")
print(f"  Guardado: {MODELS_DIR}/vuln_scorer.pkl")

# ============================================================
# MODELO 3: PatternDetector (clasificación de tipo de vuln)
# ============================================================
print("\n[3/4] Entrenando PatternDetector...")

X_train, X_test, y_train, y_test = train_test_split(descriptions, vuln_types, test_size=0.2, random_state=42)

pattern_pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
    ("clf", SGDClassifier(loss="log_loss", class_weight="balanced", random_state=42, max_iter=1000)),
])
pattern_pipeline.fit(X_train, y_train)
y_pred = pattern_pipeline.predict(X_test)
acc = (np.array(y_pred) == np.array(y_test)).mean()
print(f"  Accuracy: {acc:.3f}")

joblib.dump(pattern_pipeline, MODELS_DIR / "pattern_detector.pkl")
print(f"  Guardado: {MODELS_DIR}/pattern_detector.pkl")

# ============================================================
# MODELO 4: TargetPrioritizer
# ============================================================
print("\n[4/4] Entrenando TargetPrioritizer...")

# Features: has_auth, num_endpoints, has_api, has_db, tech_count, h1_submissions
n_targets = 500
X_priority = np.random.randint(0, 10, size=(n_targets, 6)).astype(float)
X_priority[:, 2] = np.random.randint(0, 2, n_targets)  # has_api: binario
X_priority[:, 3] = np.random.randint(0, 2, n_targets)  # has_db: binario
# Priority 1-5 correlaciona con features
raw_priority = (X_priority[:, 1] * 0.3 + X_priority[:, 4] * 0.2 +
                X_priority[:, 2] * 2 + X_priority[:, 3] * 2 + np.random.normal(0, 1, n_targets))
y_priority = np.clip(np.round(raw_priority / 2).astype(int), 1, 5)

X_train, X_test, y_train, y_test = train_test_split(X_priority, y_priority, test_size=0.2, random_state=42)

prioritizer = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
prioritizer.fit(X_train, y_train)
acc = (prioritizer.predict(X_test) == y_test).mean()
print(f"  Accuracy: {acc:.3f}")

joblib.dump(prioritizer, MODELS_DIR / "target_prioritizer.pkl")
print(f"  Guardado: {MODELS_DIR}/target_prioritizer.pkl")

# ============================================================
# Metadata de modelos
# ============================================================
import datetime
metadata = {
    "trained_at": datetime.datetime.now().isoformat(),
    "training_samples": N,
    "models": {
        "severity_classifier": {"type": "RandomForestClassifier", "classes": SEVERITIES},
        "vuln_scorer": {"type": "GradientBoostingRegressor", "output": "cvss_score_0_10"},
        "pattern_detector": {"type": "SGDClassifier", "classes": VULN_TYPES},
        "target_prioritizer": {"type": "RandomForestClassifier", "output": "priority_1_5"},
    }
}
with open(MODELS_DIR / "model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\n✅ Todos los modelos entrenados y guardados en {MODELS_DIR}")
