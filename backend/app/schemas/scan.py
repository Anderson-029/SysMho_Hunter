import uuid
from datetime import datetime

from pydantic import BaseModel


class ScanCreate(BaseModel):
    target_id: uuid.UUID
    scan_type: str = "full"  # full|recon|vuln_scan|custom
    config: dict = {}


class ScanResponse(BaseModel):
    id: uuid.UUID
    target_id: uuid.UUID
    scan_type: str
    status: str
    phase: str | None
    initiated_by: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
