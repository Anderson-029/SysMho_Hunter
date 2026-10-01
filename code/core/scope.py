"""
scope — carga y gestión del alcance autorizado (scope.txt).

El scope SIEMPRE viene de un archivo local (dominios/IPs/CIDRs/wildcards),
nunca hardcodeado. Antes de operar, el usuario confirma explícitamente que
tiene autorización; la confirmación queda registrada en session.log.
"""

from pathlib import Path

import ui_utils as ui


class ScopeError(Exception):
    pass


def load_scope(scope_path: str | Path) -> list[str]:
    """Lee scope.txt → lista de entradas (ignora comentarios y vacías)."""
    path = Path(scope_path)
    if not path.exists():
        raise ScopeError(f"Archivo de scope no encontrado: {path}")

    entries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)

    if not entries:
        raise ScopeError(f"El scope '{path}' no contiene entradas válidas.")
    return entries


def confirm_authorization(
    scope: list[str], require_typed: bool = True
) -> bool:
    """Muestra el scope y exige confirmación explícita de autorización.

    Retorna True si el usuario confirma, False si no.
    """
    ui.agente("Scope autorizado cargado:")
    for s in scope:
        ui.info(f"• {s}")
    ui.warn(
        "Solo debes operar contra objetivos para los que tienes permiso "
        "explícito y por escrito."
    )
    if require_typed:
        resp = ui.pedir_texto("Escribe CONFIRMO para continuar")
        return resp.strip().upper() == "CONFIRMO"
    return ui.preguntar("¿Confirmas que tienes autorización?", default=False)


def in_scope(target: str, scope: list[str]) -> bool:
    """Verifica si un target está dentro del scope (sin lanzar excepción)."""
    from recon.base_tool import BaseTool, ScopeViolationError

    class _Probe(BaseTool):
        async def run(self, target, scope, **kwargs):  # pragma: no cover
            ...

        def parse_output(self, raw_output):  # pragma: no cover
            return []

    try:
        return _Probe()._validate_scope(target, scope)
    except ScopeViolationError:
        return False
