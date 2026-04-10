from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id")
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    vuln_type: Mapped[str | None] = mapped_column(
        String(100)
    )  # XSS|SQLi|SSRF|RCE|IDOR|LFI|etc.
    severity: Mapped[str | None] = mapped_column(
        String(20)
    )  # critical|high|medium|low|informational
    cvss_score: Mapped[float | None] = mapped_column(Numeric(4, 1))
    cvss_vector: Mapped[str | None] = mapped_column(String(200))
    cwe_id: Mapped[str | None] = mapped_column(
        String(20)
    )  # CWE-79, CWE-89, etc.
    url: Mapped[str | None] = mapped_column(String(2000))
    parameter: Mapped[str | None] = mapped_column(String(500))
    method: Mapped[str | None] = mapped_column(String(10))
    request_raw: Mapped[str | None] = mapped_column(Text)
    response_raw: Mapped[str | None] = mapped_column(Text)
    proof_of_concept: Mapped[str | None] = mapped_column(Text)
    remediation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="new")
    # Campos ML
    ml_severity: Mapped[str | None] = mapped_column(String(20))
    ml_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    brain_reasoning: Mapped[str | None] = mapped_column(Text)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")
    target: Mapped["Target"] = relationship(
        "Target", back_populates="findings"
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="finding", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_type: Mapped[str | None] = mapped_column(
        String(50)
    )  # screenshot|request|response|log|code
    content: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    finding: Mapped["Finding"] = relationship(
        "Finding", back_populates="evidence"
    )
