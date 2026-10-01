# =============================================================================
# Autor        : SysMho
# Módulo       : ui_utils.py
# Descripción  : Componentes visuales del CLI (banner, colores, prompts).
#
# Nota legal   : Herramienta de pentesting para pruebas controladas, fines
#                educativos o auditorías con autorización explícita.
# =============================================================================

import datetime
import os
import sys

# Colores de terminal
BOLD_RED = "\033[1;31m"
BOLD_GREEN = "\033[1;32m"
BOLD_CYAN = "\033[1;36m"
YELLOW = "\033[1;33m"
GREY = "\033[0;90m"
DIM = "\033[2m"
NC = "\033[0m"

HUNTER_NAME = "agente"  # prefijo conversacional del cerebro


def check_root() -> None:
    """Algunas herramientas del arsenal requieren privilegios de root."""
    if os.geteuid() != 0:
        print(
            f"{YELLOW}[!] Aviso: varias herramientas (nmap -sS, masscan) "
            f"requieren root. Ejecuta con sudo para cobertura completa.{NC}"
        )


def agente(msg: str) -> None:
    """Imprime una línea en voz del agente (prosa conversacional)."""
    print(f"{BOLD_CYAN}[{HUNTER_NAME}]{NC} {msg}")


def info(msg: str) -> None:
    print(f"{GREY}  {msg}{NC}")


def ok(msg: str) -> None:
    print(f"{BOLD_GREEN}  ✓ {msg}{NC}")


def warn(msg: str) -> None:
    print(f"{YELLOW}  ⚠ {msg}{NC}")


def error(msg: str) -> None:
    print(f"{BOLD_RED}  ✘ {msg}{NC}")


def preguntar(pregunta: str, default: bool = True) -> bool:
    """Prompt sí/no. default=True → [S/n], default=False → [s/N]."""
    sufijo = "[S/n]" if default else "[s/N]"
    while True:
        try:
            raw = input(f"{YELLOW}  {pregunta} {sufijo}: {NC}")
            resp = raw.strip().lower()
        except EOFError:
            return default
        if resp == "":
            return default
        if resp in ("s", "y", "si", "sí"):
            return True
        if resp in ("n", "no"):
            return False


def elegir(pregunta: str, opciones: list[str]) -> int:
    """Menú numerado. Retorna el índice (0-based) de la opción elegida."""
    for i, op in enumerate(opciones, 1):
        print(f"{BOLD_CYAN}  {i}){NC} {op}")
    while True:
        try:
            resp = input(f"{YELLOW}  Elige [1-{len(opciones)}]: {NC}").strip()
        except EOFError:
            return 0
        if resp.isdigit() and 1 <= int(resp) <= len(opciones):
            return int(resp) - 1


def pedir_texto(pregunta: str) -> str:
    try:
        return input(f"{YELLOW}  {pregunta}: {NC}").strip()
    except EOFError:
        return ""


def mostrar_banner() -> None:
    print(f"{BOLD_CYAN}")
    print(
        r"""
   ___ ___ ___ _____ _  _ ___     _  _ _   _ _  _ _____ ___ ___
  / __| __/ __|_   _| || | _ \   | || | | | | \| |_   _| __| _ \
  \__ \ _|\__ \ | | | __ |   /   | __ | |_| | .` | | | | _||   /
  |___/___|___/ |_| |_||_|_|_\   |_||_|\___/|_|\_| |_| |___|_|_\
"""
    )
    print(f"{NC}", end="")
    line = "=" * 70
    print(line)
    print("  SysMho Hunter — Agente autónomo de pentesting".ljust(70))
    print("  Reconocimiento · Análisis con IA · Reportes conversacionales")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Ejecución: {ts}")
    print(line)
    print(
        f"{BOLD_RED}  [!] SOLO contra objetivos con autorización "
        f"explícita.{NC}"
    )
    print(
        f"{BOLD_RED}  [!] El uso no autorizado es ilegal y es tu "
        f"responsabilidad.{NC}"
    )
    print()


def abort(msg: str) -> None:
    error(msg)
    sys.exit(1)
