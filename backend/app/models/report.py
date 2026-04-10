from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    executive_summary: Mapped[str | None] = mapped_column(Text)
    h1_format_md: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    h1_report_id: Mapped[str | None] = mapped_column(String(100))
    bounty_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    target: Mapped["Target"] = relationship("Target")
    report_findings: Mapped[list["ReportFinding"]] = relationship(
        "ReportFinding", back_populates="report", cascade="all, delete-orphan"
    )


class ReportFinding(Base):
    __tablename__ = "report_findings"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        primary_key=True,
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id"), primary_key=True
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)

    report: Mapped["Report"] = relationship(
        "Report", back_populates="report_findings"
    )
    finding: Mapped["Finding"] = relationship("Finding")
