"""
interactive — modo guiado (-I): menú paso a paso con salida conversacional.
"""

import ui_utils as ui
from core import scope as scope_mod
from core.orchestrator import Orchestrator
from core.output import SessionOutput
from session_logger import log_event, setup_session_logger


def _target_from_entry(entry: str) -> str:
    """Deriva un target escaneable de una entrada de scope.

    Un wildcard '*.target.com' se reduce a 'target.com'.
    """
    if entry.startswith("*."):
        return entry[2:]
    return entry


async def run_interactive(scope_path: str, base_output: str) -> None:
    ui.mostrar_banner()
    ui.check_root()

    # 1. Cargar scope
    try:
        scope = scope_mod.load_scope(scope_path)
    except scope_mod.ScopeError as e:
        ui.abort(str(e))
        return

    # 2. Confirmar autorización
    if not scope_mod.confirm_authorization(scope):
        ui.abort("Autorización no confirmada. Abortando.")
        return

    # 3. Elegir objetivo
    opciones = [_target_from_entry(s) for s in scope]
    opciones_mostrar = opciones + ["(escribir otro objetivo del scope)"]
    ui.agente("¿Contra qué objetivo del scope quieres trabajar?")
    idx = ui.elegir("Objetivo", opciones_mostrar)
    if idx == len(opciones):
        target = ui.pedir_texto("Objetivo (debe estar dentro del scope)")
        if not scope_mod.in_scope(target, scope):
            ui.abort(f"'{target}' está fuera del scope. Abortando.")
            return
    else:
        target = opciones[idx]

    # 4. Preparar salida + logger de sesión
    output = SessionOutput(target, base_output)
    session_logger = setup_session_logger(output.session_log)
    log_event(
        session_logger,
        "authorized",
        f"Autorización confirmada para {target}",
        target=target,
        scope=scope,
    )
    ui.ok(f"Sesión iniciada. Evidencia en: {output.dir}")

    # 5. Ejecutar pipeline (interactivo: pregunta cada paso)
    orch = Orchestrator(target, scope, output, auto_approve=False)
    await orch.run()
