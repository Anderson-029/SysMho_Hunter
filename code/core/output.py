"""
output — gestión de evidencia en archivos locales (estilo venom).

Estructura por sesión:
    output/<target>/<YYYYMMDD_HHMMSS>/
        ├── findings.json     (todos los hallazgos estructurados)
        ├── report.md         (reporte conversacional final)
        ├── recon/            (salida cruda por herramienta)
        └── session.log       (log JSON del ciclo de vida)
"""

import json
import re
from datetime import datetime
from pathlib import Path


def _slug(target: str) -> str:
    """Normaliza un target a nombre de carpeta seguro."""
    s = re.sub(r"^https?://", "", target.strip())
    s = s.rstrip("/")
    s = re.sub(r"[^A-Za-z0-9._-]", "_", s)
    return s or "target"


class SessionOutput:
    def __init__(self, target: str, base_dir: str | Path = "output"):
        self.target = target
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dir = Path(base_dir) / _slug(target) / ts
        self.recon_dir = self.dir / "recon"
        self.recon_dir.mkdir(parents=True, exist_ok=True)

    @property
    def session_log(self) -> Path:
        return self.dir / "session.log"

    def save_findings(self, findings: list[dict]) -> Path:
        path = self.dir / "findings.json"
        path.write_text(
            json.dumps(findings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def save_report(self, markdown: str) -> Path:
        path = self.dir / "report.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def save_payloads(self, markdown: str) -> Path:
        path = self.dir / "payloads.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def save_raw(self, tool_name: str, raw_output: str) -> Path:
        path = self.recon_dir / f"{tool_name}.txt"
        path.write_text(raw_output, encoding="utf-8")
        return path
