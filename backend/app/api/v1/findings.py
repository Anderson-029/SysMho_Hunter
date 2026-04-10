import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.finding import Finding
from app.schemas.finding import FindingResponse, FindingUpdate

router = APIRouter()


@router.get("/", response_model=list[FindingResponse])
async def list_findings(
    target_id: uuid.UUID | None = Query(None),
    scan_id: uuid.UUID | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
):
    q = select(Finding).order_by(Finding.discovered_at.desc())
    if target_id:
        q = q.where(Finding.target_id == target_id)
    if scan_id:
        q = q.where(Finding.scan_id == scan_id)
    if severity:
        q = q.where(Finding.severity == severity)
    if status:
        q = q.where(Finding.status == status)
    result = await db.execute(q.limit(200))
    return result.scalars().all()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding no encontrado")
    return finding


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: uuid.UUID,
    data: FindingUpdate,
    db: AsyncSession = Depends(get_session),
):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding no encontrado")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(finding, field, value)
    await db.commit()
    await db.refresh(finding)
    return finding
