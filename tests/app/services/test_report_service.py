"""
Pruebas unitarias para ReportGenerator.
Valida la generación de Markdown profesional para reportes de seguridad.
"""

import pytest
from app.services.report_service import ReportGenerator

@pytest.fixture
def reporter():
    """Instancia el generador de reportes."""
    return ReportGenerator()

@pytest.mark.asyncio
async def test_generate_report_structure(reporter):
    """Verifica que el reporte tenga las secciones básicas de HackerOne."""
    target = "https://victim.com"
    findings = [
        {
            "title": "SQL Injection",
            "severity": "critical",
            "type": "sqli",
            "description": "Exploit available",
            "remediation": "Review code"
        },
        {
            "title": "Missing HSTS",
            "severity": "medium",
            "type": "header",
            "description": "No HSTS header",
            "remediation": "Add header"
        }
    ]
    recon_data = {
        "ports": [{"port": 80, "service": "http"}],
        "technologies": ["Apache/2.4"]
    }
    
    report = await reporter.generate(target, findings, recon_data)
    
    # Validaciones de contenido
    assert "# Reporte de Seguridad" in report
    assert f"**Objetivo:** {target}" in report
    assert "**Total de hallazgos:** 2" in report
    assert "## Resumen Ejecutivo" in report
    assert "## Información de Reconocimiento" in report
    assert "## Hallazgos Detallados" in report
    
    # Verificar orden de severidad (CRITICAL primero)
    # Buscamos el índice de los títulos
    idx_critical = report.find("CRITICAL")
    idx_medium = report.find("MEDIUM")
    assert idx_critical < idx_medium

@pytest.mark.asyncio
async def test_generate_summary_table(reporter):
    """Valida que la tabla de resumen tenga los emojis correctos."""
    findings = [{"severity": "critical"}, {"severity": "critical"}, {"severity": "low"}]
    
    summary = reporter._generate_summary(findings)
    
    assert "🔴" in summary # Critical
    assert "🔵" in summary # Low
    assert "2" in summary # Cantidad de critical
    assert "1" in summary # Cantidad de low
    assert "| Severidad | Cantidad |" in summary
