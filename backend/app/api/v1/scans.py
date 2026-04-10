import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.scan import Scan
from app.models.target import Target
from app.schemas.scan import ScanCreate, ScanResponse

router = APIRouter()


@router.get("/", response_model=list[ScanResponse])
async def list_scans(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(100)
    )
    return result.scalars().all()


@router.post("/", response_model=ScanResponse, status_code=201)
async def start_scan(
    data: ScanCreate, db: AsyncSession = Depends(get_session)
):
    target = await db.get(Target, data.target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target no encontrado")

    scan = Scan(
        target_id=data.target_id,
        scan_type=data.scan_type,
        config=data.config,
        status="pending",
        started_at=datetime.now(timezone.utc),
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Lanzar pipeline en background
    from app.services.scan_service import scan_service

    await scan_service.start_scan(scan.id, db)

    return scan


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan no encontrado")
    return scan


@router.delete("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(
    scan_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan no encontrado")
    if scan.status not in ("pending", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cancelar un scan en estado '{scan.status}'",
        )
    scan.status = "cancelled"
    scan.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(scan)
    return scan
