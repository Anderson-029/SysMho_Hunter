import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id")
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id")
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id")
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # low|medium|high|critical
    risk_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending|approved|rejected|executed|failed
    requested_by: Mapped[str] = mapped_column(String(100), default="agent")
    reviewed_by: Mapped[str | None] = mapped_column(String(100))
    review_notes: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
