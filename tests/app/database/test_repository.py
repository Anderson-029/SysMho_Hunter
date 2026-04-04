"""
Pruebas unitarias para el Repositorio de Escaneos (ScanRepository).
Valida que la capa de datos en Python interactúe correctamente con PostgreSQL.
"""

import pytest
import uuid
from app.database.repository import ScanRepository

@pytest.fixture
def repository():
    """Instancia el repositorio para cada test."""
    return ScanRepository()

@pytest.mark.asyncio
async def test_repository_upsert_and_get_target(db, repository):
    """Prueba el flujo de creación y recuperación de un objetivo."""
    target_url = "https://repo-test.com"
    hostname = "repo-test.com"
    
    # 1. Upsert
    target_id = await repository.upsert_target(hostname, target_url)
    assert target_id > 0
    
    # 2. Verificar vía consulta directa (usando el fixture db)
    row = await db.fetchrow("SELECT * FROM targets WHERE id = $1", target_id)
    assert row["hostname"] == hostname
    assert row["base_url"] == target_url

@pytest.mark.asyncio
async def test_repository_create_scan_and_get_by_uid(db, repository):
    """Prueba la creación de un escaneo y su recuperación por UID."""
    # Setup
    target_id = await repository.upsert_target("test.scan", "http://test.scan")
    scan_uid = str(uuid.uuid4())[:8]
    
    # 1. Crear escaneo
    scan_id = await repository.create_scan(scan_uid, target_id, "full")
    assert scan_id > 0
    
    # 2. Recuperar por UID
    scan = await repository.get_scan_by_uid(scan_uid)
    assert scan is not None
    assert scan["id"] == scan_id
    assert scan["scan_uid"] == scan_uid
    assert scan["target_url"] == "http://test.scan"

@pytest.mark.asyncio
async def test_repository_add_log_and_get_recent(db, repository):
    """Prueba la inserción y recuperación de logs de escaneo."""
    target_id = await repository.upsert_target("log.test", "http://log.test")
    scan_id = await db.fetchval("SELECT id FROM scans WHERE target_id = $1", target_id)
    if not scan_id:
        scan_id = await repository.create_scan("log-1", target_id)
        
    # 1. Agregar logs
    await repository.add_log(scan_id, "info", "Log de prueba 1")
    await repository.add_log(scan_id, "warning", "Log de prueba 2")
    
    # 2. Recuperar logs
    logs = await repository.get_recent_logs(scan_id, limit=10)
    assert len(logs) >= 2
    # El primero en la lista debería ser el último insertado (Log 2)
    assert logs[0]["message"] == "Log de prueba 2"
    assert str(logs[0]["level"]) == "warning"

@pytest.mark.asyncio
async def test_repository_dashboard_stats(db, repository):
    """Prueba la obtención de estadísticas globales."""
    # Limpiar o asegurar datos mínimos
    await db.execute("DELETE FROM findings")
    target_id = await repository.upsert_target("stats.repo", "http://stats.repo")
    scan_id = await repository.create_scan("s-1", target_id)
    
    await repository.add_finding(scan_id, "XSS", "Reflected XSS", "high")
    
    stats = await repository.get_dashboard_stats()
    assert stats["total_findings"] >= 1
    assert stats["high_findings"] >= 1
