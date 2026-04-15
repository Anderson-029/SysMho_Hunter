import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.target import Scope, Target
from app.schemas.target import (
    ScopeBulkImportLines,
    ScopeCreate,
    ScopeResponse,
    TargetCreate,
    TargetResponse,
    TargetUpdate,
)

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
    scopes_data = data.scopes
    data_dict = data.model_dump(exclude={"scopes"})
    target = Target(**data_dict)
    db.add(target)
    await db.flush()
    for s in scopes_data:
        db.add(Scope(target_id=target.id, **s.model_dump()))
    await db.commit()
    await db.refresh(target)
    result = await db.execute(
        select(Target)
        .options(selectinload(Target.scopes))
        .where(Target.id == target.id)
    )
    return result.scalar_one()


@router.get("/{target_id}/", response_model=TargetResponse)
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


@router.patch("/{target_id}/", response_model=TargetResponse)
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


@router.delete("/{target_id}/", status_code=204)
async def delete_target(
    target_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target no encontrado")
    await db.delete(target)
    await db.commit()


@router.post(
    "/{target_id}/scopes/",
    response_model=ScopeResponse,
    status_code=201,
)
async def add_scope(
    target_id: uuid.UUID,
    data: ScopeCreate,
    db: AsyncSession = Depends(get_session),
):
    """Agregar un scope individual a un target."""
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target no encontrado")

    scope = Scope(target_id=target_id, **data.model_dump())
    db.add(scope)
    await db.commit()
    await db.refresh(scope)
    return scope


@router.post("/{target_id}/scopes/bulk/", response_model=list[ScopeResponse])
async def bulk_import_scopes(
    target_id: uuid.UUID,
    data: ScopeBulkImportLines,
    db: AsyncSession = Depends(get_session),
):
    """
    Importar múltiples scopes desde una lista de líneas (dominios, IPs, URLs).
    Cada línea se agrega como un scope con el tipo especificado.
    """
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target no encontrado")

    scopes_created = []
    for value in data.values:
        value = value.strip()
        if not value:
            continue
        scope = Scope(
            target_id=target_id,
            scope_type=data.scope_type,
            value=value,
            is_in_scope=data.is_in_scope,
        )
        db.add(scope)
        scopes_created.append(scope)

    await db.commit()
    for scope in scopes_created:
        await db.refresh(scope)
    return scopes_created


@router.delete("/{target_id}/scopes/{scope_id}/", status_code=204)
async def delete_scope(
    target_id: uuid.UUID,
    scope_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
):
    """Eliminar un scope específico de un target."""
    result = await db.execute(
        select(Scope).where(
            Scope.id == scope_id, Scope.target_id == target_id
        )
    )
    scope = result.scalar_one_or_none()
    if not scope:
        raise HTTPException(status_code=404, detail="Scope no encontrado")
    await db.delete(scope)
    await db.commit()
