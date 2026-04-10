import uuid
from datetime import datetime

from pydantic import BaseModel


class FindingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    remediation: str | None = None


class FindingResponse(BaseModel):
    id: uuid.UUID
    scan_id: uuid.UUID | None
    target_id: uuid.UUID
    title: str
    description: str | None
    vuln_type: str | None
    severity: str | None
    cvss_score: float | None
    cwe_id: str | None
    url: str | None
    parameter: str | None
    method: str | None
    status: str
    ml_severity: str | None
    ml_confidence: float | None
    brain_reasoning: str | None
    discovered_at: datetime
    model_config = {"from_attributes": True}
