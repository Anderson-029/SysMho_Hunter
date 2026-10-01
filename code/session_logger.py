"""
session_logger — logger centralizado de la sesión.

Registra el ciclo de vida completo (scope confirmado, decisiones del cerebro,
herramientas ejecutadas, aprobaciones/rechazos, findings) en formato JSON
estructurado dentro de session.log del output de la sesión.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        if hasattr(record, "data"):
            payload["data"] = record.data
        return json.dumps(payload, ensure_ascii=False)


def setup_session_logger(log_path: Path) -> logging.Logger:
    """Configura el logger raíz para escribir JSON a session.log.

    Devuelve el logger de sesión. Idempotente por path.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("hunter")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)

    # Capturar también logs de los módulos migrados (brain, recon, rag)
    for name in ("brain", "recon", "rag", "brain.router"):
        mod_logger = logging.getLogger(name)
        mod_logger.setLevel(logging.INFO)
        mod_logger.addHandler(handler)

    return logger


def log_event(
    logger: logging.Logger, event: str, message: str, **data
) -> None:
    """Registra un evento estructurado en la sesión."""
    logger.info(message, extra={"event": event, "data": data})
