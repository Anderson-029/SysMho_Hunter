"""
Pruebas unitarias para las funciones almacenadas de PostgreSQL.
Valida la integridad de la lógica modular de base de datos.
"""

import pytest
import json

@pytest.mark.asyncio
async def test_fn_upsert_target(db):
    """Verifica que fn_upsert_target cree correctamente un nuevo objetivo."""
    target_id = await db.fetchval(
        "SELECT fn_upsert_target($1, $2, $3, $4::JSONB)",
        "example.com", "https://example.com", "93.184.216.34", '["*.example.com"]'
    )
    assert target_id is not None
    assert target_id > 0

    # Verificar persistencia
    row = await db.fetchrow("SELECT * FROM targets WHERE id = $1", target_id)
    assert row["hostname"] == "example.com"
    assert row["base_url"] == "https://example.com"

@pytest.mark.asyncio
async def test_fn_create_scan(db):
    """Verifica la creación de un escaneo vinculado a un target."""
    # Setup: Necesitamos un target primero
    target_id = await db.fetchval(
        "SELECT fn_upsert_target($1, $2)", "test.local", "http://test.local"
    )
    
    scan_uid = "test-1234"
    scan_id = await db.fetchval(
        "SELECT fn_create_scan($1, $2, $3, $4::JSONB)",
        scan_uid, target_id, "recon", '{"threads": 10}'
    )
    
    assert scan_id is not None
    row = await db.fetchrow("SELECT * FROM scans WHERE id = $1", scan_id)
    assert row["scan_uid"] == scan_uid
    assert row["status"] == "pending"

@pytest.mark.asyncio
async def test_fn_update_scan_status(db):
    """Verifica el cambio de estado y el auto-log generado."""
    target_id = await db.fetchval("SELECT fn_upsert_target($1, $2)", "os.com", "https://os.com")
    scan_id = await db.fetchval("SELECT fn_create_scan($1, $2)", "sid-99", target_id)
    
    # Actualizar a 'recon'
    await db.execute("SELECT fn_update_scan_status($1, 'recon'::scan_status)", scan_id)
    
    # Verificar status actualizado
    scan_row = await db.fetchrow("SELECT status FROM scans WHERE id = $1", scan_id)
    assert scan_row["status"] == "recon"
    
    # Verificar que se creó el log automático
    log_exists = await db.fetchval(
        "SELECT EXISTS(SELECT 1 FROM scan_logs WHERE scan_id = $1 AND message LIKE '%recon%')",
        scan_id
    )
    assert log_exists is True

@pytest.mark.asyncio
async def test_fn_add_finding_duplicate_detection(db):
    """Verifica que fn_add_finding detecte duplicados correctamente."""
    target_id = await db.fetchval("SELECT fn_upsert_target($1, $2)", "vuln.loc", "http://vuln.loc")
    scan_id = await db.fetchval("SELECT fn_create_scan($1, $2)", "scan-d", target_id)
    
    # 1. Primer hallazgo
    id1 = await db.fetchval(
        "SELECT fn_add_finding($1, $2, $3, 'high'::severity_level)",
        scan_id, "SQLi", "SQL Injection en login"
    )
    
    # 2. Re-insertar mismo hallazgo (duplicado)
    id2 = await db.fetchval(
        "SELECT fn_add_finding($1, $2, $3, 'high'::severity_level)",
        scan_id, "SQLi", "SQL Injection en login"
    )
    
    f1 = await db.fetchrow("SELECT is_duplicate FROM findings WHERE id = $1", id1)
    f2 = await db.fetchrow("SELECT is_duplicate FROM findings WHERE id = $1", id2)
    
    assert f1["is_duplicate"] is False
    assert f2["is_duplicate"] is True

@pytest.mark.asyncio
async def test_fn_get_dashboard_stats(db):
    """Verifica que las estadísticas globales del dashboard sean consistentes."""
    # Insertar algunos datos base
    target_id = await db.fetchval("SELECT fn_upsert_target($1, $2)", "stats.target", "http://stats.target")
    scan_id = await db.fetchval("SELECT fn_create_scan($1, $2)", "scan-stats", target_id)
    
    await db.execute("SELECT fn_add_finding($1, 'XSS', 'Cross Site Scripting', 'medium'::severity_level)", scan_id)
    await db.execute("SELECT fn_add_finding($1, 'CVE', 'Critical Vulnerability', 'critical'::severity_level)", scan_id)
    
    stats = await db.fetchrow("SELECT * FROM fn_get_dashboard_stats()")
    
    assert stats["total_targets"] >= 1
    assert stats["total_findings"] >= 2
    assert stats["critical_findings"] >= 1
    assert stats["medium_findings"] >= 1
