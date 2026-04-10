import uuid
from datetime import datetime

from pydantic import BaseModel


class ActionReview(BaseModel):
    decision: str  # approved|rejected
    review_notes: str | None = None


class ActionResponse(BaseModel):
    id: uuid.UUID
    action_type: str
    description: str
    risk_level: str
    risk_reason: str | None
    status: str
    requested_by: str
    reviewed_by: str | None
    review_notes: str | None
    expires_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
