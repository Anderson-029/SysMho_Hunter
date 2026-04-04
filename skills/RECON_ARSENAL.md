# Skill: Recon Arsenal — Reconocimiento Profesional

Eres experto en reconocimiento pasivo y activo para bug bounty. Conoces cada herramienta, cuándo usarla y cómo integrarla en pipelines async.

## Stack de Herramientas por Fase

### Fase 1: Descubrimiento de Superficie
| Herramienta | Propósito | Comando clave |
|---|---|---|
| `subfinder` | Subdominios pasivos (APIs públicas) | `subfinder -d target.com -silent` |
| `amass enum` | Subdominios activos + ASN | `amass enum -d target.com -passive` |
| `assetfinder` | Subdominios rápidos | `assetfinder --subs-only target.com` |
| `crt.sh` | Certificate Transparency | `curl "https://crt.sh/?q=%.target.com&output=json"` |
| `chaos` | Dataset de subdominios (ProjectDiscovery) | `chaos -d target.com -silent` |

### Fase 2: Resolución y Fingerprinting
| Herramienta | Propósito | Comando clave |
|---|---|---|
| `httpx` | Probe masivo, tech detection | `httpx -l subs.txt -tech-detect -status-code -title` |
| `nmap` | Port scanning + service version | `nmap -sV -sC -p- --min-rate 1000 target.com` |
| `nuclei` | Templates de vulnerabilidades | `nuclei -u target.com -t cves/ -t misconfigs/` |
| `whatweb` | Fingerprinting web | `whatweb -a 3 target.com` |

### Fase 3: Descubrimiento de Contenido
| Herramienta | Propósito | Comando clave |
|---|---|---|
| `ffuf` | Fuzzing dirs/files/params | `ffuf -u URL/FUZZ -w wordlist.txt -mc 200,301,302` |
| `gau` | URLs históricas (Wayback + CommonCrawl) | `gau --threads 5 target.com` |
| `waybackurls` | URLs de Wayback Machine | `waybackurls target.com` |
| `arjun` | Parameter discovery | `arjun -u https://target.com/api -m GET` |
| `LinkFinder` | Endpoints en JavaScript | `python linkfinder.py -i target.com -d` |
| `SecretFinder` | Secrets en JavaScript | `python SecretFinder.py -i https://target.com/app.js` |

### Fase 4: Inteligencia Pasiva
- **Shodan**: `shodan search "hostname:target.com"` — puertos y banners
- **FOFA**: Similar a Shodan con más datos chinos/globales
- **VirusTotal**: Subdominios y relaciones de dominio
- **GitHub Dorking**: `org:targetorg password OR secret OR api_key`

## Wordlists Recomendadas
```
/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt
/usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt
/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
```

## Pipeline Async en Python
```python
async def full_recon(target: str) -> ReconResult:
    # Fase 1: paralelo
    subdomains, cert_subs = await asyncio.gather(
        run_subfinder(target),
        query_crtsh(target)
    )
    all_subs = deduplicate(subdomains + cert_subs)
    
    # Fase 2: paralelo
    live_hosts, ports = await asyncio.gather(
        probe_httpx(all_subs),
        scan_nmap(target)
    )
    
    # Fase 3: basado en resultados previos
    endpoints = await discover_content(live_hosts)
    return ReconResult(hosts=live_hosts, ports=ports, endpoints=endpoints)
```

## Rate Limiting Anti-WAF
- Delays entre requests: 0.5-2s aleatorio
- User-Agent rotation
- IP rotation si disponible
- Respetar robots.txt en targets con restricciones
