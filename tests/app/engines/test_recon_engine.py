"""
Pruebas unitarias para ReconEngine.
Mokeamos la ejecución de comandos para validar el parseo y la lógica asíncrona.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.engines.recon_engine import ReconEngine

@pytest.fixture
def recon_engine():
    """Instancia el motor."""
    return ReconEngine()

@pytest.mark.asyncio
async def test_parse_nmap_xml(recon_engine):
    """Verifica que el XML de nmap se parsee correctamente."""
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <nmaprun>
      <host>
        <ports>
          <port protocol="tcp" portid="80"><state state="open"/><service name="http" version="2.4.41"/></port>
          <port protocol="tcp" portid="443"><state state="open"/><service name="https" version="1.1.1"/></port>
          <port protocol="tcp" portid="22"><state state="closed"/></port>
        </ports>
      </host>
    </nmaprun>"""
    
    result = recon_engine._parse_nmap_xml(xml_data)
    assert 80 in result["ports"]
    assert 443 in result["ports"]
    assert 22 not in result["ports"]
    assert len(result["services"]) == 2
    assert result["services"][0]["name"] == "http"

@pytest.mark.asyncio
async def test_scan_ports_mock(recon_engine):
    """Prueba scan_ports simulando la ejecución de nmap."""
    mock_stdout = b"""<?xml version="1.0" encoding="UTF-8"?>
    <nmaprun><host><ports><port portid="80"><state state="open"/><service name="http"/></port></ports></host></nmaprun>"""
    
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        # Configurar el mock del proceso
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (mock_stdout, b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        
        result = await recon_engine.scan_ports("localhost")
        
        assert 80 in result["ports"]
        mock_exec.assert_called_once()

@pytest.mark.asyncio
async def test_discover_directories_mock(recon_engine):
    """Prueba discover_directories simulando ffuf."""
    mock_ffuf_json = json.dumps({
        "results": [
            {"url": "http://test.com/admin", "status": 200, "length": 123},
            {"url": "http://test.com/config", "status": 301, "length": 45}
        ]
    }).encode()
    
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (mock_ffuf_json, b"")
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc
        
        result = await recon_engine.discover_directories("http://test.com")
        
        assert len(result) == 2
        assert result[0]["status"] == 200
        assert "/admin" in result[0]["url"]

@pytest.mark.asyncio
async def test_recon_engine_full_run(recon_engine):
    """Prueba una ejecución completa con mocks de todas las herramientas."""
    with patch.object(ReconEngine, "scan_ports", return_value={"ports": [80], "services": []}), \
         patch.object(ReconEngine, "discover_directories", return_value=[{"url": "/api"}]):
        
        results = await recon_engine.run_discovery("http://example.com")
        
        assert results["hostname"] == "example.com"
        assert 80 in results["ports"]
        assert len(results["directories"]) == 1
