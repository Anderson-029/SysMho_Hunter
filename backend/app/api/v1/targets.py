import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.target import Scope, Target
from app.schemas.target import TargetCreate, TargetResponse, TargetUpdate

router = APIRouter()


@router.get("/", response_model=list[TargetResponse])
async def list_targets(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Target)
        .options(selectinload(Target.scopes))
        .order_by(Target.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=TargetResponse, status_code=201)
async def create_target(
    data: TargetCreate, db: AsyncSession = Depends(get_session)
):
    target = Target(
        name=data.name,
        organization=data.organization,
        h1_program_slug=data.h1_program_slug,
        priority=data.priority,
        notes=data.notes,
    )
    db.add(target)
    await db.flush()
    for s in data.scopes:
        db.add(Scope(target_id=target.id, **s.model_dump()))
    await db.commit()
    await db.refresh(target)
    result = await db.execute(
        select(Target)
        .options(selectinload(Target.scopes))
        .where(Target.id == target.id)
    )
    return result.scalar_one()


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    result = await db.execute(
        select(Target)
        .options(selectinload(Target.scopes))
        .where(Target.id == target_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target no encontrado")
    return target


@router.patch("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: uuid.UUID,
    data: TargetUpdate,
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target no encontrado")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(target, field, value)
    await db.commit()
    result = await db.execute(
        select(Target)
        .options(selectinload(Target.scopes))
        .where(Target.id == target_id)
    )
    return result.scalar_one()


@router.delete("/{target_id}", status_code=204)
async def delete_target(
    target_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target no encontrado")
    await db.delete(target)
    await db.commit()
