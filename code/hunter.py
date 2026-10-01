#!/usr/bin/env python3
"""
SysMho Hunter — Agente autónomo de pentesting (CLI).

Modos de uso:
    # Interactivo (menú guiado + salida conversacional)
    sudo python3 hunter.py -I

    # Directo (scripts/automatización)
    sudo python3 hunter.py target.com --scope scope.txt -o output/
    sudo python3 hunter.py target.com --scope scope.txt --yes   # auto-aprueba

Nota legal: úsalo solo contra objetivos para los que tengas autorización
explícita y por escrito. El uso no autorizado es ilegal.
"""

import argparse
import asyncio
import sys

import ui_utils as ui
from core import scope as scope_mod
from core.orchestrator import Orchestrator
from core.output import SessionOutput
from session_logger import log_event, setup_session_logger


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hunter",
        description="Agente autónomo de pentesting (CLI conversacional).",
    )
    p.add_argument(
        "target",
        nargs="?",
        help="Objetivo a auditar (debe estar en el scope). "
        "Si se omite, arranca el modo interactivo.",
    )
    p.add_argument(
        "-I",
        "--interactive",
        action="store_true",
        help="Modo interactivo guiado.",
    )
    p.add_argument(
        "--scope",
        default="scope.txt",
        help="Archivo de scope autorizado (default: scope.txt).",
    )
    p.add_argument(
        "-o",
        "--output",
        default="output",
        help="Directorio base de resultados (default: output/).",
    )
    p.add_argument(
        "--phases",
        nargs="+",
        default=None,
        help="Fases a ejecutar (default: todas). "
        "Ej: subdomain_enum port_scan vuln_scan",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Auto-aprueba herramientas de riesgo bajo/medio (modo directo).",
    )
    return p


async def run_direct(args: argparse.Namespace) -> None:
    try:
        scope = scope_mod.load_scope(args.scope)
    except scope_mod.ScopeError as e:
        ui.abort(str(e))
        return

    if not scope_mod.in_scope(args.target, scope):
        ui.abort(
            f"'{args.target}' está fuera del scope en {args.scope}. Abortando."
        )
        return

    output = SessionOutput(args.target, args.output)
    session_logger = setup_session_logger(output.session_log)
    log_event(
        session_logger,
        "authorized",
        f"Target {args.target} validado contra scope",
        target=args.target,
        scope=scope,
        mode="direct",
    )
    ui.ok(f"Sesión iniciada. Evidencia en: {output.dir}")

    orch = Orchestrator(args.target, scope, output, auto_approve=args.yes)
    await orch.run(phases=args.phases)


def main() -> None:
    args = build_parser().parse_args()

    try:
        if args.interactive or not args.target:
            from cli.interactive import run_interactive

            asyncio.run(run_interactive(args.scope, args.output))
        else:
            asyncio.run(run_direct(args))
    except KeyboardInterrupt:
        print()
        ui.warn("Interrumpido por el usuario. Saliendo.")
        sys.exit(130)


if __name__ == "__main__":
    main()
