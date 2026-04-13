# 🛠️ Herramientas de Pentesting — SysMho Hunter

Este documento explica cómo instalar y verificar las herramientas necesarias para que SysMho Hunter funcione correctamente.

---

## 📋 Herramientas Requeridas

### Categoría: Base (apt/pacman/dnf)
```
✓ nmap         — Network scanning
✓ masscan      — Port scanning rápido
✓ sqlmap       — SQL injection testing
✓ nikto        — Web server scanning
✓ whatweb      — Web technology fingerprinting
✓ wfuzz        — Web fuzzing
```

### Categoría: Python (pip)
```
✓ wafw00f      — WAF detection
```

### Categoría: Go Tools
```
✓ ffuf         — Web fuzzing rápido
✓ nuclei       — Template-based scanning
✓ subfinder    — Subdomain enumeration
✓ amass        — Advanced subdomain enumeration
✓ gobuster     — Directory/DNS/VHost bruteforce
✓ gau          — GetAllUrls - URL discovery
✓ waybackurls  — Wayback machine URLs
✓ dalfox       — XSS scanner
✓ httprobe     — HTTP probe
✓ hakrawler    — Web crawler
✓ httpx        — HTTP toolkit
```

### Categoría: Cargo (Rust)
```
✓ feroxbuster  — Web content scanner (Rust)
```

---

## 🚀 Instalación Rápida

### Opción 1: Instalación Automática (RECOMENDADO)

```bash
# Instalar todas las herramientas automáticamente
bash scripts/install_tools.sh

# O con verificación y reinstalación si faltan
bash scripts/check_tools.sh --install
```

### Opción 2: Verificar sin Instalar

```bash
# Ver qué está instalado y qué falta
bash scripts/check_tools.sh

# Output ejemplo:
# ✓ nmap
# ✓ masscan
# ✗ sqlmap — FALTA
# ... etc
```

---

## 📊 Verificación Antes de Ejecutar Scans

**SysMho Hunter verifica automáticamente** las herramientas cuando ejecutas:

```bash
bash labs/sysmho_integration.sh auto devil 172.17.0.2 80
```

Output:
```
[i] Verificando herramientas de pentesting...
✓ Backend disponible (http://localhost:8000)
✓ API Key obtenida
✓ Todas las herramientas disponibles
```

Si faltan herramientas, verás:
```
[!] Algunas herramientas faltan
[i] Para instalarlas automáticamente:
    bash scripts/check_tools.sh --install
[!] El scan podría fallar si faltan herramientas críticas
```

---

## 🔧 Instalación Manual por Distro

### Kali Linux / Parrot OS
```bash
# Herramientas base
sudo apt-get update
sudo apt-get install -y nmap masscan sqlmap nikto whatweb wfuzz

# Python
sudo pip3 install wafw00f

# Go (si no está instalado)
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Go tools
go install github.com/ffuf/ffuf/v2@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
# ... etc (ver install_tools.sh para todos)
```

### Arch Linux / Manjaro
```bash
# Herramientas base
sudo pacman -S nmap masscan sqlmap nikto whatweb wfuzz

# Python
sudo pip install wafw00f

# Go tools
go install github.com/ffuf/ffuf/v2@latest
# ... etc
```

### Ubuntu / Debian
```bash
# Igual a Kali/Parrot (usa apt-get)
# Algunos paquetes pueden no estar disponibles
# En ese caso, instalar via Go o desde fuente
```

---

## 🎯 Flujo Completo Recomendado

```
1. Verificar qué falta:
   bash scripts/check_tools.sh

2. Instalar automáticamente:
   bash scripts/check_tools.sh --install

3. Verificar nuevamente:
   bash scripts/check_tools.sh

4. Ejecutar integration.sh:
   bash labs/sysmho_integration.sh auto devil 172.17.0.2 80
```

---

## ❓ Troubleshooting

### "Go no instalado"
```bash
# Solución: Instalar Go
# Descarga desde https://go.dev/dl/
# O usando apt:
sudo apt-get install golang-go
```

### "feroxbuster: command not found"
```bash
# Requiere Rust/Cargo
# Instala desde: https://www.rust-lang.org/tools/install
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install feroxbuster
```

### "wafw00f: command not found"
```bash
# Requiere Python 3 + pip
sudo apt-get install python3 python3-pip
sudo pip3 install wafw00f
```

### "nuclei: permission denied"
```bash
# El archivo no tiene permisos de ejecución
# Solución:
export PATH="$HOME/go/bin:$PATH"
# O reinstala:
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

---

## 📝 Notas Importantes

- **SysMho Hunter NO falla si faltan herramientas**, solo advierte
- Si ejecutas un scan sin herramientas críticas, el scan fallará silenciosamente
- Es responsabilidad del usuario verificar que las herramientas están listas ANTES de scans
- Para debugging, revisa los logs del backend en `/tmp/backend.log`

---

## 🔗 Referencias

- Herramienta de verificación: `scripts/check_tools.sh`
- Instalador automático: `scripts/install_tools.sh`
- Integration script: `labs/sysmho_integration.sh`

---

**Última actualización:** 12 Abril 2026  
**Compatible con:** Kali Linux, Parrot OS, Arch Linux, Ubuntu, Debian
