# Metodología de Reconocimiento

## Orden de Ejecución

### Paso 1 — Recon Pasivo (sin tocar el target)
```bash
# Subdominios
subfinder -d TARGET -o recon/subdomains_subfinder.txt
amass enum -passive -d TARGET -o recon/subdomains_amass.txt
cat recon/subdomains_*.txt | sort -u > recon/subdomains_all.txt

# DNS
whois TARGET
dig TARGET ANY
dnsrecon -d TARGET
```

### Paso 2 — Verificar qué está vivo
```bash
httpx -l recon/subdomains_all.txt \
  -title -tech-detect -status-code \
  -o recon/alive.txt
```

### Paso 3 — Port Scanning
```bash
# Rápido primero
rustscan -a TARGET --range 1-65535 -- -sV -sC -o recon/ports_rustscan.txt

# Detallado en puertos interesantes
nmap -sV -sC -p PORT1,PORT2 TARGET -o recon/ports_nmap.txt
```

### Paso 4 — Detección Automática de Vulnerabilidades
```bash
nuclei -u TARGET \
  -t ~/nuclei-templates/ \
  -severity critical,high,medium \
  -o recon/nuclei_findings.txt

nikto -h TARGET -o recon/nikto.txt
```

### Paso 5 — Fuzzing de Directorios/Endpoints
```bash
ffuf -u https://TARGET/FUZZ \
  -w /opt/SecLists/Discovery/Web-Content/common.txt \
  -o recon/ffuf_dirs.txt

gobuster dir -u https://TARGET \
  -w /opt/SecLists/Discovery/Web-Content/big.txt \
  -o recon/gobuster.txt
```

### Paso 6 — OSINT Enriquecido
```bash
shodan search hostname:TARGET
theHarvester -d TARGET -b all
```

## Qué Buscar por Tecnología

### Aplicaciones Web
- Login forms → credential stuffing, brute force
- Parámetros URL → SQLi, LFI, SSRF
- File uploads → unrestricted upload, RCE
- APIs → IDOR, broken auth, mass assignment
- Headers → security misconfigs, info disclosure

### Servicios de Red
| Puerto | Servicio | Qué probar |
|--------|----------|------------|
| 21 | FTP | anonymous login, bounce attack |
| 22 | SSH | weak creds, version exploits |
| 80/443 | HTTP/S | web vulns completo |
| 445 | SMB | eternalblue, null sessions |
| 3306 | MySQL | default creds, UDF injection |
| 8080/8443 | Alt HTTP | admin panels, dev configs |

## Estructura de Carpetas por Target
```
~/recon/
└── TARGET/
    └── YYYYMMDD/
        ├── subdomains_all.txt
        ├── alive.txt
        ├── ports_rustscan.txt
        ├── ports_nmap.txt
        ├── nuclei_findings.txt
        ├── ffuf_dirs.txt
        └── notes.md        ← hallazgos manuales
```

## Herramientas Complementarias
- **gowitness** — screenshots automáticos de todos los subdominios vivos
- **waybackurls** — URLs históricas del target (endpoints olvidados)
- **gau** — URLs de múltiples fuentes (wayback, OTX, etc.)
- **hakrawler** — crawling rápido de la app
- **paramspider** — extraer parámetros de URLs históricas
