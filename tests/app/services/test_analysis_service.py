"""
Pruebas unitarias para VulnAnalyzer.
Valida la detección lógica de vulnerabilidades comunes sin necesidad de IA.
"""

import pytest
from app.services.analysis_service import VulnAnalyzer

@pytest.fixture
def analyzer():
    """Instancia el analizador para cada test."""
    return VulnAnalyzer()

@pytest.mark.asyncio
async def test_analyze_missing_headers(analyzer):
    """Verifica la detección de cabeceras de seguridad faltantes."""
    recon_data = {
        "headers": {
            "Server": "Apache",
            "Content-Type": "text/html"
        }
    }
    
    findings = await analyzer.analyze("http://test.com", recon_data)
    
    # Debería detectar HSTS, CSP, X-Frame-Options, etc.
    header_findings = [f for f in findings if f["type"] == "missing_header"]
    assert len(header_findings) >= 5
    
    titles = [f["title"] for f in header_findings]
    assert "Cabecera de seguridad faltante: Strict-Transport-Security" in titles
    assert "Cabecera de seguridad faltante: Content-Security-Policy" in titles

@pytest.mark.asyncio
async def test_analyze_exposed_services(analyzer):
    """Verifica la detección de servicios riesgosos expuestos."""
    recon_data = {
        "services": [
            {"name": "http", "port": 80},
            {"name": "postgresql", "port": 5432},
            {"name": "redis", "port": 6379}
        ]
    }
    
    findings = await analyzer.analyze("http://test.com", recon_data)
    
    service_findings = [f for f in findings if f["type"] == "exposed_service"]
    assert len(service_findings) == 2
    
    severities = [f["severity"] for f in service_findings]
    assert "high" in severities # postgresql
    assert "critical" in severities # redis

@pytest.mark.asyncio
async def test_analyze_sensitive_directories(analyzer):
    """Verifica el descubrimiento de directorios/archivos sensibles."""
    recon_data = {
        "directories": [
            {"url": "http://test.com/index.php", "status": 200},
            {"url": "http://test.com/.git/config", "status": 200},
            {"url": "http://test.com/backup.zip", "status": 200}
        ]
    }
    
    findings = await analyzer.analyze("http://test.com", recon_data)
    
    dir_findings = [f for f in findings if f["type"] == "sensitive_directory"]
    assert len(dir_findings) == 2
    
    titles = [f["title"] for f in dir_findings]
    assert any(".git/config" in t for t in titles)
    assert any("backup.zip" in t for t in titles)
    assert all(f["severity"] == "high" for f in dir_findings)
