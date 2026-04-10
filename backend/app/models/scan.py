from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False
    )
    scan_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    phase: Mapped[str | None] = mapped_column(String(100))
    initiated_by: Mapped[str] = mapped_column(String(100), default="agent")
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    target: Mapped["Target"] = relationship("Target", back_populates="scans")
    tasks: Mapped[list["ScanTask"]] = relationship(
        "ScanTask", back_populates="scan", cascade="all, delete-orphan"
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding", back_populates="scan"
    )
    logs: Mapped[list["AgentLog"]] = relationship(
        "AgentLog", back_populates="scan"
    )
    reasoning: Mapped[list["BrainReasoning"]] = relationship(
        "BrainReasoning", back_populates="scan"
    )


class ScanTask(Base):
    __tablename__ = "scan_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    target_value: Mapped[str] = mapped_column(String(500), nullable=False)
    command: Mapped[str | None] = mapped_column(Text)
    stdout: Mapped[str | None] = mapped_column(Text)
    stderr: Mapped[str | None] = mapped_column(Text)
    exit_code: Mapped[int | None] = mapped_column(SmallInteger)
    raw_output_path: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="tasks")
