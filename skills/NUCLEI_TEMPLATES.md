# Skill: Nuclei Templates — Detección Automatizada de Vulnerabilidades

Eres experto en Nuclei (ProjectDiscovery). Sabes ejecutarlo, escribir templates y usarlo dentro de pipelines async en Python.

## Ejecución desde Python (async)
```python
async def run_nuclei(target: str, templates: List[str], severity: List[str]) -> List[NucleiFinding]:
    cmd = [
        "nuclei",
        "-u", target,
        "-t", ",".join(templates),
        "-severity", ",".join(severity),
        "-json",              # output JSON por línea
        "-silent",
        "-rate-limit", "50", # requests/segundo
        "-timeout", "10",
        "-no-color"
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    findings = []
    async for line in proc.stdout:
        try:
            data = json.loads(line.decode().strip())
            findings.append(NucleiFinding.from_json(data))
        except json.JSONDecodeError:
            continue
    await proc.wait()
    return findings
```

## Templates Prioritarios para Bug Bounty
```yaml
# Categorías más rentables
cves/            # CVEs conocidos con PoC
misconfigs/      # Configuraciones incorrectas (high bounty)
  - misconfigs/aws/         # S3 buckets públicos, metadata
  - misconfigs/nginx/       # alias traversal, misconfig
  - misconfigs/apache/
exposures/       # Archivos expuestos (.env, .git, backup)
takeovers/       # Subdomain takeover (fácil bounty)
technologies/    # Fingerprinting para guiar análisis
vulnerabilities/ # Vulns genéricas (XSS, SQLi, SSRF)
```

## Template Personalizado — Ejemplo
```yaml
id: custom-exposed-env-file
info:
  name: Exposed .env File with Secrets
  author: SysMho_Hunter
  severity: high
  tags: exposure, secrets, misconfiguration

requests:
  - method: GET
    path:
      - "{{BaseURL}}/.env"
      - "{{BaseURL}}/.env.production"
      - "{{BaseURL}}/.env.local"
    
    matchers-condition: and
    matchers:
      - type: word
        words:
          - "APP_KEY="
          - "DB_PASSWORD="
          - "AWS_SECRET"
        condition: or
      - type: status
        status:
          - 200
    
    extractors:
      - type: regex
        name: secrets
        regex:
          - "([A-Z_]+)=(.+)"
```

## Integración con ScanService
```python
# En analysis_service.py
NUCLEI_SCAN_PROFILES = {
    "quick": {
        "templates": ["technologies/", "exposures/", "takeovers/"],
        "severity": ["critical", "high"]
    },
    "deep": {
        "templates": ["cves/", "misconfigs/", "vulnerabilities/"],
        "severity": ["critical", "high", "medium"]
    },
    "full": {
        "templates": ["cves/", "misconfigs/", "exposures/", 
                      "vulnerabilities/", "takeovers/"],
        "severity": ["critical", "high", "medium", "low"]
    }
}
```

## Actualización de Templates
```bash
nuclei -update-templates   # actualizar a la última versión
nuclei -update            # actualizar nuclei binario
```
