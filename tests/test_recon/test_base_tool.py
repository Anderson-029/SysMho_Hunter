"""
test_base_tool.py — Tests de BaseTool (validación de scope en memoria).

El scope enforcement es la salvaguarda central del CLI: valida el objetivo
contra la lista cargada de scope.txt antes de ejecutar cualquier herramienta.
"""

import pytest

from recon.base_tool import BaseTool, ScopeViolationError, ToolResult


class DummyTool(BaseTool):
    name = "dummy"
    binary = "dummy"
    phase = "subdomain_enum"
    risk_level = "low"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            success=True,
            raw_output="",
            stderr="",
            exit_code=0,
        )

    def parse_output(self, raw: str) -> list[dict]:
        return []


class TestValidateScope:
    """Valida _validate_scope(target, scope_list) — en memoria, sin BD."""

    def test_dominio_exacto_pasa(self):
        assert DummyTool()._validate_scope("testcorp.com", ["testcorp.com"])

    def test_dominio_fuera_de_scope_lanza_error(self):
        with pytest.raises(ScopeViolationError):
            DummyTool()._validate_scope("evilcorp.com", ["testcorp.com"])

    def test_wildcard_subdominio_pasa(self):
        assert DummyTool()._validate_scope(
            "api.testcorp.com", ["*.testcorp.com"]
        )

    def test_wildcard_dominio_raiz_pasa(self):
        assert DummyTool()._validate_scope("testcorp.com", ["*.testcorp.com"])

    def test_ip_en_cidr_pasa(self):
        assert DummyTool()._validate_scope("192.168.1.50", ["192.168.1.0/24"])

    def test_ip_fuera_de_cidr_lanza_error(self):
        with pytest.raises(ScopeViolationError):
            DummyTool()._validate_scope("10.0.0.1", ["192.168.1.0/24"])

    def test_url_completa_extrae_host(self):
        assert DummyTool()._validate_scope(
            "https://testcorp.com/login", ["testcorp.com"]
        )

    def test_scope_vacio_lanza_error(self):
        with pytest.raises(ScopeViolationError):
            DummyTool()._validate_scope("testcorp.com", [])

    def test_comentarios_y_vacios_se_ignoran(self):
        scope = ["# comentario", "", "testcorp.com"]
        assert DummyTool()._validate_scope("testcorp.com", scope)
