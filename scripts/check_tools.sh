#!/usr/bin/env bash

##############################################################################
# SysMho Hunter — Verificador de Herramientas de Pentesting
#
# Verifica que todas las herramientas requeridas estén instaladas
# Uso: bash scripts/check_tools.sh [--install]
#
# Sin args: solo reporta estado
# --install: intenta instalar las faltantes (requiere sudo)
##############################################################################

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Funciones de logging
log_ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_err()  { echo -e "${RED}[✗]${NC} $1"; }
log_info() { echo -e "${CYAN}[i]${NC} $1"; }

# Variables globales
MISSING_TOOLS=()
INSTALLED_TOOLS=()
TOTAL_TOOLS=0
AUTO_INSTALL=${1:-}

# Herramientas requeridas por categoría
declare -A TOOLS=(
    # Base (apt/pacman/dnf)
    [nmap]="base"
    [masscan]="base"
    [sqlmap]="base"
    [nikto]="base"
    [whatweb]="base"
    [wfuzz]="base"

    # Python (pip)
    [wafw00f]="pip"

    # Go tools
    [ffuf]="go"
    [feroxbuster]="cargo"
    [nuclei]="go"
    [subfinder]="go"
    [amass]="go"
    [gobuster]="go"
    [gau]="go"
    [waybackurls]="go"
    [dalfox]="go"
    [httprobe]="go"
    [hakrawler]="go"
    [httpx]="go"
)

# Detectar distro
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)

# Verificar herramienta
check_tool() {
    local tool=$1

    if which "$tool" &>/dev/null; then
        log_ok "$tool"
        INSTALLED_TOOLS+=("$tool")
        return 0
    else
        log_err "$tool — FALTA"
        MISSING_TOOLS+=("$tool")
        return 1
    fi
}

# Instalar herramientas faltantes
install_missing() {
    if [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
        log_ok "Todas las herramientas instaladas ✓"
        return 0
    fi

    log_warn "Faltantes: ${#MISSING_TOOLS[@]} herramientas"
    echo ""

    if [ "$AUTO_INSTALL" != "--install" ]; then
        log_info "Ejecuta con --install para instalar automáticamente:"
        log_info "  bash scripts/check_tools.sh --install"
        return 1
    fi

    # Instalar via install_tools.sh
    log_info "Ejecutando install_tools.sh..."
    bash scripts/install_tools.sh

    # Re-verificar
    echo ""
    log_info "Re-verificando herramientas..."
    MISSING_TOOLS=()
    INSTALLED_TOOLS=()

    for tool in "${!TOOLS[@]}"; do
        check_tool "$tool" || true
    done

    if [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
        log_ok "Todas las herramientas instaladas ✓"
        return 0
    else
        log_err "Aún faltan ${#MISSING_TOOLS[@]} herramientas:"
        for tool in "${MISSING_TOOLS[@]}"; do
            echo "  - $tool"
        done
        return 1
    fi
}

# Mostrar resumen
show_summary() {
    echo ""
    echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  Resumen de Herramientas${NC}"
    echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════${NC}\n"

    TOTAL_TOOLS=${#TOOLS[@]}
    INSTALLED_COUNT=${#INSTALLED_TOOLS[@]}
    MISSING_COUNT=${#MISSING_TOOLS[@]}

    echo -e "Distro detectada: ${BOLD}${DISTRO}${NC}"
    echo -e "Total herramientas: ${BOLD}${TOTAL_TOOLS}${NC}"
    echo -e "${GREEN}Instaladas: ${INSTALLED_COUNT}${NC}"
    echo -e "${RED}Faltantes: ${MISSING_COUNT}${NC}"
    echo ""

    if [ $MISSING_COUNT -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ TODAS LAS HERRAMIENTAS DISPONIBLES${NC}"
        echo -e "Listo para ejecutar scans con ${CYAN}integration.sh${NC}"
        return 0
    else
        echo -e "${RED}${BOLD}✗ HERRAMIENTAS FALTANTES:${NC}"
        for tool in "${MISSING_TOOLS[@]}"; do
            echo -e "  ${RED}•${NC} $tool (${TOOLS[$tool]})"
        done
        echo ""
        echo -e "${YELLOW}Soluciona con:${NC}"
        echo -e "  ${BOLD}bash scripts/check_tools.sh --install${NC}"
        return 1
    fi
}

# Verificar dependencias del sistema (Go, Cargo, Python)
check_dependencies() {
    echo -e "\n${BOLD}${BLUE}Dependencias del Sistema:${NC}"

    if which go &>/dev/null; then
        log_ok "Go instalado"
    else
        log_warn "Go NO instalado (necesario para herramientas Go)"
        log_info "Instala desde: https://go.dev/dl/"
    fi

    if which cargo &>/dev/null; then
        log_ok "Cargo instalado"
    else
        log_warn "Cargo NO instalado (necesario para feroxbuster)"
    fi

    if which python3 &>/dev/null; then
        log_ok "Python 3 instalado"
    else
        log_err "Python 3 NO instalado"
    fi
}

# Main
main() {
    echo -e "\n${BOLD}${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║   SysMho Hunter — Verificador de Herramientas      ║${NC}"
    echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════╝${NC}\n"

    # Verificar cada herramienta
    for tool in "${!TOOLS[@]}"; do
        check_tool "$tool" || true
    done

    # Mostrar dependencias
    check_dependencies

    # Mostrar resumen
    show_summary
    local summary_exit=$?

    # Instalar si falta y se solicita
    if [ $summary_exit -ne 0 ] && [ "$AUTO_INSTALL" = "--install" ]; then
        echo ""
        install_missing
        show_summary
    fi
}

# Ejecutar
main "$@"
