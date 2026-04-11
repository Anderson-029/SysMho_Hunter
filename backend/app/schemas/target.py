import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScopeCreate(BaseModel):
    scope_type: str = Field(..., pattern="^(domain|ip|cidr|url|wildcard)$")
    value: str
    is_in_scope: bool = True
    notes: str | None = None


class ScopeBulkImport(BaseModel):
    scopes: list[ScopeCreate]


class ScopeBulkImportLines(BaseModel):
    """Importar desde líneas de texto (una URL/dominio por línea)"""

    values: list[str] = Field(
        ..., description="Lista de dominios, IPs, URLs o CIDRs"
    )
    scope_type: str = Field(
        "domain", pattern="^(domain|ip|cidr|url|wildcard)$"
    )
    is_in_scope: bool = True


class ScopeResponse(ScopeCreate):
    id: uuid.UUID
    target_id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class TargetCreate(BaseModel):
    name: str
    organization: str | None = None
    h1_program_slug: str | None = None
    priority: int = Field(5, ge=1, le=10)
    notes: str | None = None
    platform: str | None = None
    program_url: str | None = None
    rules_md: str | None = None
    bounty_table: dict | None = None
    out_of_scope_notes: str | None = None
    safe_harbor: bool = True
    scopes: list[ScopeCreate] = []


class TargetUpdate(BaseModel):
    name: str | None = None
    organization: str | None = None
    h1_program_slug: str | None = None
    status: str | None = None
    priority: int | None = Field(None, ge=1, le=10)
    notes: str | None = None
    platform: str | None = None
    program_url: str | None = None
    rules_md: str | None = None
    bounty_table: dict | None = None
    out_of_scope_notes: str | None = None
    safe_harbor: bool | None = None


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
    rules_md: str | None
    bounty_table: dict | None
    out_of_scope_notes: str | None
    safe_harbor: bool
    created_at: datetime
    scopes: list[ScopeResponse] = []
    model_config = {"from_attributes": True}
