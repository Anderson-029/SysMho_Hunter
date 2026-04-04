"""
Pruebas unitarias maestras para ScanService.
Utiliza inyección de dependencias con Mocks para validar la orquestación del pipeline.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.scan_service import ScanService

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.upsert_target.return_value = 1
    repo.create_scan.return_value = 10
    repo.get_scan_by_uid.return_value = {"id": 10, "status": "completed"}
    repo.get_recent_logs.return_value = []
    repo.get_findings.return_value = []
    return repo

@pytest.fixture
def mock_recon():
    recon = AsyncMock()
    recon.run_discovery.return_value = {"ports": [80], "directories": []}
    return recon

@pytest.fixture
def mock_analyzer():
    analyzer = AsyncMock()
    # Retorna un hallazgo de ejemplo
    analyzer.analyze.return_value = [{
        "type": "test_vuln", 
        "title": "Test Vuln", 
        "severity": "high"
    }]
    return analyzer

@pytest.fixture
def mock_reporter():
    reporter = AsyncMock()
    reporter.generate.return_value = "# Report Meta"
    return reporter

@pytest.fixture
def scan_service(mock_repo, mock_recon, mock_analyzer, mock_reporter):
    """Instancia el servicio inyectando los mocks."""
    return ScanService(
        repository=mock_repo,
        recon_engine=mock_recon,
        analyzer=mock_analyzer,
        reporter=mock_reporter
    )

@pytest.mark.asyncio
async def test_start_scan_orchestration(scan_service, mock_repo):
    """Valida que el inicio del escaneo orqueste los pasos iniciales en DB."""
    uid = await scan_service.start_scan("http://victim.com")
    
    assert len(uid) == 8
    mock_repo.upsert_target.assert_called_once()
    mock_repo.create_scan.assert_called_once()
    mock_repo.add_log.assert_called()

@pytest.mark.asyncio
async def test_full_pipeline_execution(scan_service, mock_repo, mock_recon, mock_analyzer, mock_reporter):
    """Valida la ejecución del pipeline completo (Recon -> Analyze -> Report)."""
    # Ejecutamos el pipeline directamente para esperar a que termine (normalmente corre en background)
    await scan_service._run_pipeline(
        scan_id=1,
        scan_uid="test-123",
        target_url="http://victim.com",
        scan_type="full"
    )
    
    # 1. Verificar Recon
    mock_recon.run_discovery.assert_called_once()
    mock_repo.save_recon_data.assert_called_once()
    
    # 2. Verificar Análisis
    mock_analyzer.analyze.assert_called_once()
    mock_repo.add_finding.assert_called_once()
    
    # 3. Verificar Reporte
    mock_reporter.generate.assert_called_once()
    mock_repo.save_report.assert_called_once()
    
    # 4. Verificar Finalización
    # Se debe haber llamado a update_scan_status con 'completed' al final
    last_status_call = mock_repo.update_scan_status.call_args_list[-1]
    assert last_status_call.args[1] == "completed"

@pytest.mark.asyncio
async def test_pipeline_failure_handling(scan_service, mock_repo, mock_recon):
    """Valida que los errores en el pipeline se registren correctamente en DB."""
    # Forzar error en recon
    mock_recon.run_discovery.side_effect = Exception("Crash in recon tools")
    
    await scan_service._run_pipeline(1, "uid-fail", "http://fail.com", "full")
    
    # Verificar que se marcó como failed
    last_status_call = mock_repo.update_scan_status.call_args_list[-1]
    assert last_status_call.args[1] == "failed"
    # Verificar que se logueó el error
    mock_repo.add_log.assert_called_with(1, "error", "Falla crítica: Crash in recon tools")
