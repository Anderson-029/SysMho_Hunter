"""
SysMho Hunter - Endpoints de la API v1.
Basado en Arquitectura Limpia e Inyección de Dependencias.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl

from app.services.scan_service import ScanService

router = APIRouter(tags=["scanner"])

# Inyección de dependencia para el servicio
def get_scan_service() -> ScanService:
    return ScanService()

class ScanRequest(BaseModel):
    target_url: HttpUrl
    scope: Optional[List[str]] = None
    scan_type: str = "full"

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str

@router.post("/scan/start", response_model=ScanResponse)
async def start_scan(
    request: ScanRequest, 
    service: ScanService = Depends(get_scan_service)
) -> ScanResponse:
    """Inicia un nuevo escaneo contra el target."""
    try:
        scan_id = await service.start_scan(
            target_url=str(request.target_url),
            scope=request.scope,
            scan_type=request.scan_type
        )
        return ScanResponse(
            scan_id=scan_id,
            status="running",
            message=f"Escaneo iniciado contra {request.target_url}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scan/{scan_id}/status")
async def get_scan_status(
    scan_id: str, 
    service: ScanService = Depends(get_scan_service)
) -> dict:
    """Obtiene el estado actual y logs de un escaneo."""
    status = await service.get_status(scan_id)
    if not status:
        raise HTTPException(status_code=404, detail="Escaneo no encontrado")
    return status

@router.get("/scan/{scan_id}/findings")
async def get_findings(
    scan_id: str, 
    service: ScanService = Depends(get_scan_service)
) -> dict:
    """Obtiene los hallazgos detallados de un escaneo."""
    findings = await service.get_findings(scan_id)
    return {"scan_id": scan_id, "findings": findings}

@router.get("/scans")
async def list_scans(service: ScanService = Depends(get_scan_service)) -> dict:
    """Lista el historial de todos los escaneos."""
    scans = await service.list_scans()
    return {"scans": scans}

@router.get("/dashboard/stats")
async def dashboard_stats(service: ScanService = Depends(get_scan_service)) -> dict:
    """Estadísticas globales para el Dashboard."""
    return await service.get_dashboard_stats()
