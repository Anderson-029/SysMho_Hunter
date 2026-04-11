import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# BOUNTY TIERS
# ─────────────────────────────────────────────────────────────────────────────


class BountyRange(BaseModel):
    """Rango de recompensa por severidad (min/max/avg en USD)."""

    min: int | None = None
    max: int | None = None
    avg: int | None = None


class BountyTierTable(BaseModel):
    """Tabla de bounty por severidad para un tier."""

    low: BountyRange | None = None
    medium: BountyRange | None = None
    high: BountyRange | None = None
    critical: BountyRange | None = None


class BountyTiers(BaseModel):
    """Tiers de recompensa (Primary y Secondary como en H1)."""

    primary: BountyTierTable | None = None
    secondary: BountyTierTable | None = None


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVE CAMPAIGN
# ─────────────────────────────────────────────────────────────────────────────


class CampaignMultipliers(BaseModel):
    """Multiplicadores de bounty por severidad durante campaña."""

    low: float | None = None
    medium: float | None = None
    high: float | None = None
    critical: float | None = None


class ActiveCampaign(BaseModel):
    """Campaña activa del programa de bug bounty."""

    end_date: str | None = None  # "2026-04-23"
    description: str | None = None
    asset_count: int | None = None
    bounty_multipliers: CampaignMultipliers | None = None


# ─────────────────────────────────────────────────────────────────────────────
# SCOPE
# ─────────────────────────────────────────────────────────────────────────────


class ScopeCreate(BaseModel):
    scope_type: str = Field(..., pattern="^(domain|ip|cidr|url|wildcard)$")
    value: str
    is_in_scope: bool = True
    tier: str | None = Field(None, pattern="^(primary|secondary)$")
    notes: str | None = None


class ScopeBulkImport(BaseModel):
    scopes: list[ScopeCreate]


class ScopeBulkImportLines(BaseModel):
    """Importar desde líneas de texto (una URL/dominio por línea)."""

    values: list[str] = Field(
        ..., description="Lista de dominios, IPs, URLs o CIDRs"
    )
    scope_type: str = Field(
        "domain", pattern="^(domain|ip|cidr|url|wildcard)$"
    )
    is_in_scope: bool = True
    tier: str | None = Field(None, pattern="^(primary|secondary)$")


class ScopeResponse(ScopeCreate):
    id: uuid.UUID
    target_id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# TARGET
# ─────────────────────────────────────────────────────────────────────────────


class TargetCreate(BaseModel):
    # Identificación básica
    name: str
    organization: str | None = None
    h1_program_slug: str | None = None
    # hackerone|bugcrowd|intigriti|yeswehack
    platform: str | None = None
    program_url: str | None = None
    priority: int = Field(5, ge=1, le=10)
    notes: str | None = None

    # Contenido del programa
    introduction_md: str | None = None  # Texto de bienvenida
    rules_md: str | None = None  # Reglas de engagement
    disclosure_policy: str | None = None
    out_of_scope_notes: str | None = None
    safe_harbor: bool = True

    # Badges y features
    program_features: list[str] | None = None
    program_tags: list[str] | None = None

    # Métricas de respuesta
    response_efficiency_pct: float | None = Field(None, ge=0, le=100)
    avg_response_hours: float | None = None
    avg_triage_hours: float | None = None
    avg_bounty_hours: float | None = None
    avg_resolution_hours: float | None = None

    # Recompensas
    bounty_tiers: BountyTiers | None = None

    # Campaña activa
    active_campaign: ActiveCampaign | None = None

    # Vulnerabilidades prioritarias
    focus_areas: list[str] | None = None

    # Scopes iniciales
    scopes: list[ScopeCreate] = []


class TargetUpdate(BaseModel):
    # Identificación básica
    name: str | None = None
    organization: str | None = None
    h1_program_slug: str | None = None
    platform: str | None = None
    program_url: str | None = None
    status: str | None = None
    priority: int | None = Field(None, ge=1, le=10)
    notes: str | None = None

    # Contenido del programa
    introduction_md: str | None = None
    rules_md: str | None = None
    disclosure_policy: str | None = None
    out_of_scope_notes: str | None = None
    safe_harbor: bool | None = None

    # Badges y features
    program_features: list[str] | None = None
    program_tags: list[str] | None = None

    # Métricas de respuesta
    response_efficiency_pct: float | None = Field(None, ge=0, le=100)
    avg_response_hours: float | None = None
    avg_triage_hours: float | None = None
    avg_bounty_hours: float | None = None
    avg_resolution_hours: float | None = None

    # Recompensas
    bounty_tiers: BountyTiers | None = None

    # Campaña activa
    active_campaign: ActiveCampaign | None = None

    # Vulnerabilidades prioritarias
    focus_areas: list[str] | None = None


class TargetResponse(BaseModel):
    id: uuid.UUID
    name: str
    organization: str | None
    h1_program_slug: str | None
    status: str
    priority: int
    notes: str | None
    platform: str | None
    program_url: str | None

    # Contenido del programa
    introduction_md: str | None
    rules_md: str | None
    disclosure_policy: str | None
    out_of_scope_notes: str | None
    safe_harbor: bool

    # Badges y features
    program_features: list[str] | None
    program_tags: list[str] | None

    # Métricas de respuesta
    response_efficiency_pct: float | None
    avg_response_hours: float | None
    avg_triage_hours: float | None
    avg_bounty_hours: float | None
    avg_resolution_hours: float | None

    # Recompensas
    bounty_tiers: BountyTiers | None

    # Campaña activa
    active_campaign: ActiveCampaign | None

    # Vulnerabilidades prioritarias
    focus_areas: list[str] | None

    created_at: datetime
    scopes: list[ScopeResponse] = []
    model_config = {"from_attributes": True}
