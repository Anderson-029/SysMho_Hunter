# Scripts, Payloads & Herramientas Ofensivas

## Regla de Oro
Todo script ofensivo debe tener: **scope check + logging + modo seguro por defecto.**
Si falta cualquiera de los tres → no está terminado.

## Estructura de un Script Ofensivo

### Template Python
```python
#!/usr/bin/env python3
"""
Descripción: Qué hace este script
Uso: python3 script.py --target URL --scope programa.json
Autor: Anderson
"""
import argparse
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'/tmp/script_{datetime.now():%Y%m%d_%H%M%S}.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

def validate_scope(target: str, scope_file: str) -> bool:
    """Siempre validar antes de ejecutar."""
    # cargar scope y verificar
    ...

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--scope', required=True)
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostrar qué haría sin ejecutar')
    args = parser.parse_args()

    if not validate_scope(args.target, args.scope):
        log.error(f"Target {args.target} fuera de scope. Abortando.")
        sys.exit(1)

    if args.dry_run:
        log.info("[DRY-RUN] Mostraría acciones sin ejecutar")
        return

    # lógica real aquí

if __name__ == '__main__':
    main()
```

### Template Bash
```bash
#!/bin/bash
set -euo pipefail

TARGET="${1:?Uso: $0 <target> <scope>}"
SCOPE="${2:?Uso: $0 <target> <scope>}"
OUTPUT_DIR="$HOME/recon/$TARGET/$(date +%Y%m%d_%H%M%S)"
LOG="$OUTPUT_DIR/run.log"

mkdir -p "$OUTPUT_DIR"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

# Scope check obligatorio
if ! grep -q "$TARGET" "$SCOPE" 2>/dev/null; then
    log "ERROR: $TARGET no está en scope. Abortando."
    exit 1
fi

log "Iniciando contra $TARGET"
log "Output: $OUTPUT_DIR"
```

## Categorías de Payloads

### Convenciones de Naming
```
payloads/
├── sqli/
│   ├── error_based.txt
│   ├── blind_time.txt
│   └── union_select.txt
├── xss/
│   ├── basic.txt
│   ├── bypass_filters.txt
│   └── stored.txt
├── lfi/
├── rce/
├── ssrf/
└── auth/
    ├── default_creds.txt
    └── bypass_headers.txt
```

### Niveles de Agresividad
| Nivel | Descripción | Requiere |
|-------|-------------|----------|
| `safe` | Solo lectura, no modifica nada | Scope validado |
| `active` | Envía requests activos, no destructivo | Scope + confirmación |
| `aggressive` | Puede causar errores/logs en target | Scope + confirmación explícita |
| `destructive` | Puede modificar/eliminar datos | **NUNCA** sin aprobación manual |

### Default siempre: `safe` o `active`
Nunca comenzar en `aggressive` o `destructive`.

## Organización de Outputs
```
~/recon/
└── TARGET_DOMAIN/
    └── YYYYMMDD_HHMMSS/
        ├── run.log          ← log de ejecución
        ├── subdomains.txt   ← subfinder + amass
        ├── alive.txt        ← httpx results
        ├── ports.txt        ← nmap/rustscan
        ├── nuclei.txt       ← nuclei findings
        ├── requests/        ← curl/http logs importantes
        └── screenshots/     ← gowitness si aplica
```

## Reglas al Escribir Payloads
- Comentar qué vulnerabilidad explota y por qué funciona
- Incluir variante de bypass si el básico no funciona
- Probar siempre en entorno local/laboratorio antes de usar en producción
- No incluir payloads que destruyan datos (DROP TABLE, rm -rf, etc.) sin flag explícito

## Herramientas para Desarrollo de Scripts
- **pwntools** — exploits binarios, CTF
- **impacket** — protocolos Windows/SMB
- **scapy** — manipulación de paquetes
- **requests + bs4** — scraping/web automation
- **paramiko** — SSH scripting
