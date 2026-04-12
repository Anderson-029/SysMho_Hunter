"""
test_base_tool.py — Tests de BaseTool y sus métodos críticos.

Cubre:
- await_approval: aprobado, rechazado, timeout, action no encontrada
- _validate_scope (sync): dominio, wildcard, CIDR, fuera de scope
- _validate_scope_from_db (async): valida contra BD, target inexistente
"""

import asyncio
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import PendingAction
from app.models.target import Scope, Target
from app.recon.base_tool import (
    APPROVAL_POLL_INTERVAL,
    BaseTool,
    ScopeViolationError,
    ToolResult,
)


# ── Tool concreta mínima para poder instanciar BaseTool ─────────────
class DummyTool(BaseTool):
    name = "dummy"
    binary = "dummy"
    phase = "recon"
    risk_level = "low"

    async def run(self, target: str, **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            raw_output="",
            stderr="",
            exit_code=0,
        )

    def parse_output(self, raw: str) -> list[dict]:
        return []


# ── Helpers ──────────────────────────────────────────────────────────

async def _make_action(
    db: AsyncSession,
    target_id: uuid.UUID,
    status: str = "pending",
) -> PendingAction:
    action = PendingAction(
        id=uuid.uuid4(),
        action_type="command_approval",
        description="test action",
        target_id=target_id,
        payload={"tool_name": "dummy"},
        risk_level="low",
        risk_reason="test",
        requested_by="agent",
        status=status,
    )
    db.add(action)
    await db.commit()
    return action


async def _make_target_with_scope(
    db: AsyncSession,
    scope_type: str,
    scope_value: str,
) -> Target:
    target = Target(
        id=uuid.uuid4(),
        name="Scope Test Target",
        organization="TestCorp",
        status="active",
        priority=5,
    )
    db.add(target)
    await db.flush()

    scope = Scope(
        id=uuid.uuid4(),
        target_id=target.id,
        scope_type=scope_type,
        value=scope_value,
        is_in_scope=True,
    )
    db.add(scope)
    await db.commit()
    return target


# ══════════════════════════════════════════════════════════════════════
# await_approval
# ══════════════════════════════════════════════════════════════════════

class TestAwaitApproval:
    """Pruebas del polling de aprobación."""

    async def test_aprobada_inmediatamente(
        self, db: AsyncSession, sample_target: Target
    ):
        """Si la acción ya está aprobada, retorna True al primer poll."""
        action = await _make_action(db, sample_target.id, status="approved")
        tool = DummyTool()
        result = await tool.await_approval(str(action.id), db, timeout_secs=10)
        assert result is True

    async def test_rechazada_inmediatamente(
        self, db: AsyncSession, sample_target: Target
    ):
        """Si la acción ya está rechazada, retorna False al primer poll."""
        action = await _make_action(db, sample_target.id, status="rejected")
        tool = DummyTool()
        result = await tool.await_approval(str(action.id), db, timeout_secs=10)
        assert result is False

    async def test_timeout_retorna_false(
        self, db: AsyncSession, sample_target: Target
    ):
        """Si la acción nunca sale de 'pending', retorna False al agotar tiempo."""
        action = await _make_action(db, sample_target.id, status="pending")
        tool = DummyTool()
        result = await tool.await_approval(
            str(action.id), db, timeout_secs=APPROVAL_POLL_INTERVAL - 1
        )
        assert result is False

    async def test_action_no_encontrada_retorna_false(
        self, db: AsyncSession
    ):
        """Si el action_id no existe en BD, retorna False sin crash."""
        tool = DummyTool()
        result = await tool.await_approval(
            str(uuid.uuid4()), db, timeout_secs=10
        )
        assert result is False

    async def test_aprobada_despues_de_espera(
        self, db: AsyncSession, sample_target: Target
    ):
        """Aprobación llega después del primer poll — debe detectarla."""
        action = await _make_action(db, sample_target.id, status="pending")
        tool = DummyTool()

        async def _approve_after_delay():
            await asyncio.sleep(APPROVAL_POLL_INTERVAL + 1)
            action.status = "approved"
            await db.commit()

        task = asyncio.create_task(_approve_after_delay())
        result = await tool.await_approval(
            str(action.id), db, timeout_secs=APPROVAL_POLL_INTERVAL * 3
        )
        await task
        assert result is True


# ══════════════════════════════════════════════════════════════════════
# _validate_scope (síncrono — lista de strings)
# ══════════════════════════════════════════════════════════════════════

class TestValidateScopeSync:
    """Valida el método _validate_scope(target, scope_list) — sin BD."""

    def test_dominio_exacto_pasa(self):
        tool = DummyTool()
        result = tool._validate_scope("testcorp.com", ["testcorp.com"])
        assert result is True

    def test_dominio_fuera_de_scope_lanza_error(self):
        tool = DummyTool()
        with pytest.raises(ScopeViolationError):
            tool._validate_scope("evilcorp.com", ["testcorp.com"])

    def test_wildcard_subdominio_pasa(self):
        tool = DummyTool()
        result = tool._validate_scope(
            "api.testcorp.com", ["*.testcorp.com"]
        )
        assert result is True

    def test_wildcard_dominio_raiz_pasa(self):
        """El dominio raíz también debe pasar con wildcard *.example.com."""
        tool = DummyTool()
        result = tool._validate_scope("testcorp.com", ["*.testcorp.com"])
        assert result is True

    def test_ip_en_cidr_pasa(self):
        tool = DummyTool()
        result = tool._validate_scope("192.168.1.50", ["192.168.1.0/24"])
        assert result is True

    def test_ip_fuera_de_cidr_lanza_error(self):
        tool = DummyTool()
        with pytest.raises(ScopeViolationError):
            tool._validate_scope("10.0.0.1", ["192.168.1.0/24"])

    def test_url_completa_extrae_host(self):
        """Con una URL completa debe extraer el hostname para validar."""
        tool = DummyTool()
        result = tool._validate_scope(
            "https://testcorp.com/login", ["testcorp.com"]
        )
        assert result is True

    def test_scope_vacio_lanza_error(self):
        tool = DummyTool()
        with pytest.raises(ScopeViolationError):
            tool._validate_scope("testcorp.com", [])


# ══════════════════════════════════════════════════════════════════════
# _validate_scope_from_db (async — valida contra BD)
# ══════════════════════════════════════════════════════════════════════

class TestValidateScopeFromDB:
    """Valida _validate_scope_from_db(target, target_id, db)."""

    async def test_dominio_en_scope_bd_pasa(self, db: AsyncSession):
        target = await _make_target_with_scope(db, "domain", "testcorp.com")
        tool = DummyTool()
        result = await tool._validate_scope_from_db(
            "testcorp.com", target.id, db
        )
        assert result is True

    async def test_subdominio_wildcard_bd_pasa(self, db: AsyncSession):
        target = await _make_target_with_scope(
            db, "wildcard", "*.testcorp.com"
        )
        tool = DummyTool()
        result = await tool._validate_scope_from_db(
            "api.testcorp.com", target.id, db
        )
        assert result is True

    async def test_dominio_fuera_scope_bd_lanza_error(self, db: AsyncSession):
        target = await _make_target_with_scope(db, "domain", "testcorp.com")
        tool = DummyTool()
        with pytest.raises(ScopeViolationError):
            await tool._validate_scope_from_db(
                "evilcorp.com", target.id, db
            )

    async def test_ip_en_cidr_bd_pasa(self, db: AsyncSession):
        target = await _make_target_with_scope(
            db, "cidr", "192.168.1.0/24"
        )
        tool = DummyTool()
        result = await tool._validate_scope_from_db(
            "192.168.1.50", target.id, db
        )
        assert result is True

    async def test_target_no_existe_lanza_error(self, db: AsyncSession):
        """Un target_id inexistente lanza ScopeViolationError."""
        tool = DummyTool()
        with pytest.raises(ScopeViolationError):
            await tool._validate_scope_from_db(
                "testcorp.com", uuid.uuid4(), db
            )
