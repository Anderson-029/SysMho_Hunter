from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255))
    h1_program_slug: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="active")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    notes: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(
        String(50)
    )  # hackerone, bugcrowd, intigriti, yeswehack
    program_url: Mapped[str | None] = mapped_column(String(500))

    # Texto de bienvenida/introducción del programa
    introduction_md: Mapped[str | None] = mapped_column(Text)

    # Reglas de engagement y políticas
    rules_md: Mapped[str | None] = mapped_column(Text)
    disclosure_policy: Mapped[str | None] = mapped_column(Text)
    out_of_scope_notes: Mapped[str | None] = mapped_column(Text)
    safe_harbor: Mapped[bool] = mapped_column(Boolean, default=True)

    # Badges y features del programa (JSON list)
    # ej: ["fast_payment","gold_safe_harbor","managed_by_h1"]
    program_features: Mapped[list | None] = mapped_column(JSON)
    # ej: ["Managed by HackerOne","Collaboration Enabled"]
    program_tags: Mapped[list | None] = mapped_column(JSON)

    # Métricas de respuesta del programa (en horas)
    response_efficiency_pct: Mapped[float | None] = mapped_column(Float)
    avg_response_hours: Mapped[float | None] = mapped_column(Float)
    avg_triage_hours: Mapped[float | None] = mapped_column(Float)
    avg_bounty_hours: Mapped[float | None] = mapped_column(Float)
    avg_resolution_hours: Mapped[float | None] = mapped_column(Float)

    # Recompensas estructuradas por tiers (Primary / Secondary)
    # ej: {"primary": {"low": {"min": 200, "max": 350}}}
    bounty_tiers: Mapped[dict | None] = mapped_column(JSON)

    # Campaña activa del programa (si aplica)
    # ej: {"end_date": "2026-04-23", "bounty_multipliers": {"critical": 2}}
    active_campaign: Mapped[dict | None] = mapped_column(JSON)

    # Tipos de vulnerabilidades priorizadas
    # ej: ["RCE","Auth Bypass","SQLi","SSRF","XSS"]
    focus_areas: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scopes: Mapped[list["Scope"]] = relationship(
        "Scope", back_populates="target", cascade="all, delete-orphan"
    )
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="target")
    findings: Mapped[list["Finding"]] = relationship(
        "Finding", back_populates="target"
    )


class Scope(Base):
    __tablename__ = "scopes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # domain|ip|cidr|url|wildcard
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    is_in_scope: Mapped[bool] = mapped_column(Boolean, default=True)
    tier: Mapped[str | None] = mapped_column(String(20))  # primary|secondary
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    target: Mapped["Target"] = relationship("Target", back_populates="scopes")
