import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.finding import Finding
from app.models.report import Report, ReportFinding
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter()


@router.get("/", response_model=list[ReportResponse])
async def list_reports(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(
    data: ReportCreate, db: AsyncSession = Depends(get_session)
):
    report = Report(target_id=data.target_id, title=data.title)
    db.add(report)
    await db.flush()
    for idx, fid in enumerate(data.finding_ids):
        finding = await db.get(Finding, fid)
        if finding:
            db.add(
                ReportFinding(
                    report_id=report.id, finding_id=fid, sort_order=idx
                )
            )
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/latest", response_model=ReportResponse)
async def get_latest_report(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc()).limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=404, detail="No hay reportes generados"
        )
    return report


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return report


@router.post("/{report_id}/generate")
async def generate_report(
    report_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    """Genera el reporte HackerOne con el cerebro de IA."""
    from app.services.report_service import report_service

    try:
        md = await report_service.generate_h1_report(str(report_id), db)
        return {"status": "generated", "chars": len(md), "preview": md[:500]}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/latest/quality-check")
async def quality_check_latest(db: AsyncSession = Depends(get_session)):
    """Evalúa la calidad del último reporte para HackerOne."""
    from app.services.report_service import report_service

    result = await db.execute(
        select(Report).order_by(Report.created_at.desc()).limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="No hay reportes")
    return await report_service.check_h1_quality(str(report.id), db)


@router.get("/{report_id}/markdown")
async def get_report_markdown(
    report_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    """Retorna el Markdown del reporte para exportar o submitear a H1."""
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if not report.h1_format_md:
        raise HTTPException(
            status_code=400,
            detail="Reporte no generado aún. Usa POST /{id}/generate",
        )
    return {"markdown": report.h1_format_md}
