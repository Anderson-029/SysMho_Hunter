import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.action import PendingAction
from app.schemas.action import ActionResponse, ActionReview

router = APIRouter()


@router.get("/", response_model=list[ActionResponse])
async def list_pending_actions(db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(PendingAction)
        .where(PendingAction.status == "pending")
        .order_by(PendingAction.created_at.asc())
    )
    return result.scalars().all()


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: uuid.UUID, db: AsyncSession = Depends(get_session)
):
    action = await db.get(PendingAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    return action


@router.post("/{action_id}/review", response_model=ActionResponse)
async def review_action(
    action_id: uuid.UUID,
    data: ActionReview,
    db: AsyncSession = Depends(get_session),
):
    action = await db.get(PendingAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    if action.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Acción ya procesada: {action.status}"
        )
    if data.decision not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400, detail="decision debe ser 'approved' o 'rejected'"
        )

    action.status = data.decision
    action.reviewed_by = "operator"
    action.review_notes = data.review_notes
    await db.commit()
    await db.refresh(action)
    return action
