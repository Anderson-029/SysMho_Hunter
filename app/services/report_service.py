"""
SysMho Hunter - Generador de Reportes.

Genera reportes profesionales en formato Markdown,
optimizados para plataformas de Bug Bounty como
HackerOne, Bugcrowd e Intigriti.
"""

from datetime import datetime
from typing import Any, Optional


class ReportGenerator:
    """Generador de reportes de seguridad en Markdown."""

    SEVERITY_ORDER = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "info": 4,
    }

    def __init__(self) -> None:
        """Inicializa el generador de reportes."""
        pass

    async def generate(
        self,
        target: str,
        findings: list[dict[str, Any]],
        recon_data: dict[str, Any],
    ) -> str:
        """
        Genera un reporte completo en formato Markdown.

        Args:
            target: URL del objetivo escaneado.
            findings: Lista de vulnerabilidades encontradas.
            recon_data: Datos del reconocimiento.

        Returns:
            Reporte formateado en Markdown.
        """
        # Ordenar hallazgos por severidad
        sorted_findings = sorted(
            findings,
            key=lambda f: self.SEVERITY_ORDER.get(
                f.get("severity", "info"), 4
            ),
        )

        report_lines = [
            f"# Reporte de Seguridad - SysMho Hunter",
            f"",
            f"**Objetivo:** {target}",
            f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Total de hallazgos:** {len(findings)}",
            f"",
            f"---",
            f"",
            f"## Resumen Ejecutivo",
            f"",
            self._generate_summary(sorted_findings),
            f"",
            f"---",
            f"",
            f"## Información de Reconocimiento",
            f"",
            self._format_recon(recon_data),
            f"",
            f"---",
            f"",
            f"## Hallazgos Detallados",
            f"",
        ]

        for i, finding in enumerate(sorted_findings, 1):
            report_lines.append(
                self._format_finding(i, finding)
            )
            report_lines.append("")

        return "\n".join(report_lines)

    def _generate_summary(
        self, findings: list[dict[str, Any]]
    ) -> str:
        """Genera un resumen con conteo por severidad."""
        counts: dict[str, int] = {}
        for finding in findings:
            severity = finding.get("severity", "info")
            counts[severity] = counts.get(severity, 0) + 1

        lines = ["| Severidad | Cantidad |", "|-----------|----------|"]
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = counts.get(severity, 0)
            if count > 0:
                emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵",
                    "info": "⚪",
                }.get(severity, "⚪")
                lines.append(
                    f"| {emoji} {severity.upper()} | {count} |"
                )

        return "\n".join(lines)

    def _format_recon(
        self, recon_data: dict[str, Any]
    ) -> str:
        """Formatea los datos de reconocimiento."""
        lines = []

        ports = recon_data.get("ports", [])
        if ports:
            lines.append("### Puertos Abiertos")
            lines.append("| Puerto | Protocolo | Servicio | Versión |")
            lines.append("|--------|-----------|----------|---------|")
            for port in ports:
                lines.append(
                    f"| {port.get('port')} "
                    f"| {port.get('protocol', 'tcp')} "
                    f"| {port.get('service', 'N/A')} "
                    f"| {port.get('version', 'N/A')} |"
                )
            lines.append("")

        tech = recon_data.get("technologies", [])
        if tech:
            lines.append("### Tecnologías Detectadas")
            for t in tech:
                lines.append(f"- {t}")
            lines.append("")

        return "\n".join(lines)

    def _format_finding(
        self, index: int, finding: dict[str, Any]
    ) -> str:
        """Formatea un hallazgo individual para el reporte."""
        severity = finding.get("severity", "info").upper()
        emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🔵",
            "INFO": "⚪",
        }.get(severity, "⚪")

        lines = [
            f"### {index}. {emoji} [{severity}] "
            f"{finding.get('title', 'Sin título')}",
            f"",
            f"**Tipo:** {finding.get('type', 'N/A')}",
            f"",
            f"**Descripción:**",
            f"{finding.get('description', 'Sin descripción.')}",
            f"",
            f"**Remediación:**",
            f"{finding.get('remediation', 'Sin remediación sugerida.')}",
            f"",
        ]

        return "\n".join(lines)
