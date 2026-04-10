"""
ReportService — genera reportes profesionales para HackerOne.
Usa el cerebro nivel 3 (Gemini/Claude) para redactar cada sección.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.router import brain_router
from app.models.finding import Finding
from app.models.report import Report, ReportFinding

logger = logging.getLogger(__name__)

SEVERITY_CVSS = {
    "critical": (9.0, 10.0),
    "high": (7.0, 8.9),
    "medium": (4.0, 6.9),
    "low": (1.0, 3.9),
    "informational": (0.0, 0.9),
}


class ReportService:
    async def generate_h1_report(
        self,
        report_id: str,
        db: AsyncSession,
    ) -> str:
        """
        Genera el reporte HackerOne completo para un report_id dado.
        Retorna el Markdown formateado.
        """
        report = await db.get(Report, report_id)
        if not report:
            raise ValueError(f"Report {report_id} no encontrado")

        # Obtener los findings del reporte
        result = await db.execute(
            select(ReportFinding)
            .where(ReportFinding.report_id == report_id)
            .order_by(ReportFinding.sort_order)
        )
        report_findings = result.scalars().all()

        if not report_findings:
            return (
                "# Reporte vacío\n\nNo hay findings asociados a este reporte."
            )

        findings = []
        for rf in report_findings:
            finding = await db.get(Finding, rf.finding_id)
            if finding:
                findings.append(finding)

        # Usar el cerebro para redactar cada finding
        sections = []
        for finding in findings:
            finding_dict = {
                "title": finding.title,
                "vuln_type": finding.vuln_type,
                "severity": finding.severity or finding.ml_severity,
                "url": finding.url,
                "description": finding.description,
                "proof_of_concept": finding.proof_of_concept,
                "cvss_score": float(finding.cvss_score)
                if finding.cvss_score
                else None,
                "cwe_id": finding.cwe_id,
                "remediation": finding.remediation,
            }
            try:
                brain_result = await brain_router.route(
                    task_type="draft_report",
                    input_data={
                        "target": str(report.target_id),
                        "finding": finding_dict,
                    },
                )
                section_md = brain_result.get("text", "")
                if not section_md:
                    section_md = self._fallback_report(finding_dict)
            except Exception as e:
                logger.warning(f"[Report] Error generando sección: {e}")
                section_md = self._fallback_report(finding_dict)

            sections.append(section_md)

        # Construir reporte completo
        severity = findings[0].severity if findings else "medium"
        report_md = self._build_full_report(
            report.title, sections, findings, severity
        )

        # Guardar en BD
        report.h1_format_md = report_md
        report.executive_summary = (
            f"Reporte con {len(findings)} hallazgo(s)."
            f" Severidad máxima: {severity}."
        )
        report.status = "ready"
        report.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return report_md

    def _build_full_report(
        self,
        title: str,
        sections: list[str],
        findings: list,
        max_severity: str,
    ) -> str:
        header = f"""# {title}

**Severidad:** {max_severity.upper()}
**Total de hallazgos:** {len(findings)}
**Generado por:** SysMho Hunter v0.2.0
**Fecha:** {datetime.now().strftime("%Y-%m-%d")}

---
"""
        return header + "\n\n---\n\n".join(sections)

    def _fallback_report(self, finding: dict) -> str:
        """Reporte básico cuando el cerebro no está disponible."""
        return f"""## {finding.get("title", "Vulnerability Found")}

**Severity:** {finding.get("severity", "medium").upper()}
**CWE:** {finding.get("cwe_id", "N/A")}
**CVSS Score:** {finding.get("cvss_score", "N/A")}

## Summary
{finding.get("description", "A security vulnerability was identified.")}

## Impact
This vulnerability could allow an attacker to compromise the affected system.

## Steps to Reproduce
1. Navigate to: `{finding.get("url", "affected endpoint")}`
2. {finding.get("proof_of_concept", "Reproduce as described.")}

## Remediation
{finding.get("remediation", "Apply security patches.")}
"""

    async def check_h1_quality(self, report_id: str, db: AsyncSession) -> dict:
        """Evalúa la calidad del reporte para HackerOne (0-10)."""
        report = await db.get(Report, report_id)
        if not report or not report.h1_format_md:
            return {"score": 0, "issues": ["Reporte no generado"]}

        md = report.h1_format_md
        issues = []
        score = 10

        required_sections = [
            "## Summary",
            "## Impact",
            "## Steps to Reproduce",
            "## Remediation",
        ]
        for section in required_sections:
            if section not in md:
                issues.append(f"Falta sección: {section}")
                score -= 2

        if len(md) < 500:
            issues.append("Reporte demasiado corto (< 500 chars)")
            score -= 2

        return {
            "score": max(0, score),
            "issues": issues,
            "ready": score >= 7,
        }


report_service = ReportService()
