"""
SysMho Hunter - Rutas de la API REST.

Define los endpoints para iniciar escaneos, consultar
resultados y gestionar el scope de los targets.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from src.core.scanner import ScanManager

router = APIRouter(tags=["scanner"])

# Instancia global del gestor de escaneos
scan_manager = ScanManager()


class ScanRequest(BaseModel):
    """Modelo de solicitud para iniciar un escaneo."""

    target_url: HttpUrl
    scope: Optional[list[str]] = None
    scan_type: str = "full"  # full, recon, fuzz, vuln


class ScanResponse(BaseModel):
    """Modelo de respuesta de un escaneo."""

    scan_id: str
    status: str
    message: str


@router.post("/scan/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest) -> ScanResponse:
    """Inicia un nuevo escaneo contra el target especificado."""
    try:
        scan_id = await scan_manager.start_scan(
            target_url=str(request.target_url),
            scope=request.scope,
            scan_type=request.scan_type,
        )
        return ScanResponse(
            scan_id=scan_id,
            status="running",
            message=f"Escaneo iniciado contra {request.target_url}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str) -> dict:
    """Obtiene el estado actual de un escaneo."""
    status = await scan_manager.get_status(scan_id)
    if not status:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")
    return status


@router.get("/scan/{scan_id}/findings")
async def get_findings(scan_id: str) -> dict:
    """Obtiene los hallazgos de un escaneo."""
    findings = await scan_manager.get_findings(scan_id)
    if findings is None:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")
    return {"scan_id": scan_id, "findings": findings}


@router.get("/scans")
async def list_scans() -> dict:
    """Lista todos los escaneos realizados."""
    scans = await scan_manager.list_scans()
    return {"scans": scans}


@router.get("/dashboard/stats")
async def dashboard_stats() -> dict:
    """Obtiene estadísticas globales para el dashboard."""
    stats = await scan_manager.get_dashboard_stats()
    return stats
