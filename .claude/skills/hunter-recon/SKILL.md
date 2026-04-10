---
name: hunter-recon
description: Estado del arsenal ofensivo — herramientas instaladas vs pendientes, fases disponibles. Úsalo antes de planificar expansión del arsenal o cuando quieras saber qué tools están listas.
---

Verifica el estado de todas las herramientas del arsenal:

```bash
echo "=== ARSENAL SYSMHO HUNTER ==="
tools=(
  "nmap:port_scan"
  "ffuf:vuln_scan"
  "feroxbuster:vuln_scan"
  "nuclei:vuln_scan"
  "subfinder:subdomain_enum"
  "amass:subdomain_enum"
  "gobuster:vuln_scan"
  "sqlmap:exploit"
  "nikto:vuln_scan"
  "whatweb:web_fingerprint"
  "wafw00f:web_fingerprint"
  "gau:crawl"
  "waybackurls:crawl"
  "dalfox:vuln_scan"
  "masscan:port_scan"
  "httprobe:web_fingerprint"
  "hakrawler:crawl"
  "eyewitness:web_fingerprint"
  "wfuzz:vuln_scan"
)

installed=0; missing=0
for entry in "${tools[@]}"; do
  tool="${entry%%:*}"; phase="${entry##*:}"
  if which "$tool" &>/dev/null; then
    version=$(${tool} --version 2>&1 | head -1 | cut -c1-40)
    echo "  ✅ $tool ($phase) — $version"
    ((installed++))
  else
    echo "  ❌ $tool ($phase) — NO INSTALADO"
    ((missing++))
  fi
done
echo ""
echo "Instaladas: $installed | Faltantes: $missing"
```
