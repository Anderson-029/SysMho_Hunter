import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportCreate(BaseModel):
    target_id: uuid.UUID
    title: str
    finding_ids: list[uuid.UUID] = []


class ReportResponse(BaseModel):
    id: uuid.UUID
    target_id: uuid.UUID
    title: str
    executive_summary: str | None
    h1_format_md: str | None
    status: str
    h1_report_id: str | None
    bounty_amount: float | None
    submitted_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
