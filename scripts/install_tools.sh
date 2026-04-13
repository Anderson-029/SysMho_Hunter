#!/usr/bin/env bash
# ============================================================
# SysMho Hunter — Instalador de herramientas de pentesting
# Detecta el sistema operativo y usa el gestor de paquetes
# apropiado. Compatible con Kali, Parrot, Ubuntu, Arch.
# ============================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_err()  { echo -e "${RED}[✗]${NC} $1"; }

# Detectar distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

install_pkg() {
    case "$DISTRO" in
        kali|parrot|ubuntu|debian) sudo apt-get install -y "$@" 2>/dev/null ;;
        arch|manjaro) sudo pacman -S --noconfirm "$@" 2>/dev/null ;;
        fedora) sudo dnf install -y "$@" 2>/dev/null ;;
        *) log_warn "Distro no reconocida: $DISTRO. Instala manualmente: $*" ;;
    esac
}

install_go_tool() {
    local tool=$1; local pkg=$2
    if ! which "$tool" &>/dev/null; then
        log_warn "Instalando $tool via go install (esto puede tardar, verás la salida)..."
        go install -v "$pkg" && log_ok "$tool instalado" || log_err "Fallo instalando $tool"
    else
        log_ok "$tool ya instalado"
    fi
}

echo "=== SysMho Hunter — Instalación de Arsenal ==="
echo "Distro detectada: $DISTRO"
echo ""

# --- Herramientas de sistema ---
echo "--- Herramientas base ---"
for tool in nmap masscan sqlmap nikto whatweb wfuzz; do
    if which "$tool" &>/dev/null; then
        log_ok "$tool ya instalado"
    else
        log_warn "Instalando $tool..."
        install_pkg "$tool"
        which "$tool" &>/dev/null && log_ok "$tool instalado" || log_err "Fallo: $tool"
    fi
done

# wafw00f (pipx para evitar conflictos con el sistema)
if ! which wafw00f &>/dev/null; then
    log_warn "Instalando wafw00f via pipx..."
    if ! which pipx &>/dev/null; then
        log_err "pipx no encontrado. Instálalo con: sudo apt install pipx && pipx ensurepath"
    else
        pipx install wafw00f && log_ok "wafw00f instalado via pipx" || log_err "Fallo: wafw00f"
    fi
else
    log_ok "wafw00f ya instalado"
fi

# eyewitness
if ! which eyewitness &>/dev/null && ! which EyeWitness &>/dev/null; then
    log_warn "eyewitness requiere instalación manual: https://github.com/RedSiege/EyeWitness"
else
    log_ok "eyewitness ya instalado"
fi

# --- Herramientas Go ---
echo ""
echo "--- Herramientas Go ---"
if ! which go &>/dev/null; then
    log_warn "Go no instalado. Las herramientas Go se omitirán."
    log_warn "Instala Go desde: https://go.dev/dl/"
else
    GO_TOOLS=(
        "ffuf:github.com/ffuf/ffuf/v2@latest"
        "feroxbuster::cargo"
        "nuclei:github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
        "subfinder:github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
        "amass:github.com/owasp-amass/amass/v4/...@master"
        "gobuster:github.com/OJ/gobuster/v3@latest"
        "gau:github.com/lc/gau/v2/cmd/gau@latest"
        "waybackurls:github.com/tomnomnom/waybackurls@latest"
        "dalfox:github.com/hahwul/dalfox/v2@latest"
        "httprobe:github.com/tomnomnom/httprobe@latest"
        "hakrawler:github.com/hakluke/hakrawler@latest"
    )

    for entry in "${GO_TOOLS[@]}"; do
        tool="${entry%%:*}"; pkg="${entry##*:}"
        if [ "$pkg" = "cargo" ]; then
            # feroxbuster se instala via cargo
            if ! which feroxbuster &>/dev/null; then
                log_warn "feroxbuster requiere cargo (Rust): cargo install feroxbuster"
            else
                log_ok "feroxbuster ya instalado"
            fi
        else
            install_go_tool "$tool" "$pkg"
        fi
    done
fi

echo ""
echo "=== Resumen final ==="
tools=(nmap masscan sqlmap nikto whatweb wfuzz wafw00f ffuf feroxbuster nuclei subfinder amass gobuster gau waybackurls dalfox httprobe hakrawler)
for tool in "${tools[@]}"; do
    which "$tool" &>/dev/null && log_ok "$tool" || log_err "$tool — NO DISPONIBLE"
done
