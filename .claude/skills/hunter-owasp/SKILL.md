---
name: hunter-owasp
description: Auditoría de seguridad completa — OWASP Top 10, MITRE ATT&CK, PTES y CWE. Analiza código backend (Python) y frontend (TypeScript) buscando vulnerabilidades reales. Úsalo antes de operar contra targets reales en bug bounty.
---

Eres un auditor de seguridad experto. Vas a auditar SysMho Hunter usando los siguientes estándares:
- **OWASP Top 10 (2021):** A01–A10
- **MITRE ATT&CK:** Tácticas relevantes para herramientas de pentesting (T1059, T1078, T1190, T1552, etc.)
- **CWE Top 25:** Debilidades más peligrosas del software
- **PTES (Penetration Testing Execution Standard):** Manejo seguro de payloads y resultados

---

## PASO 1 — Recolección de contexto

```bash
find /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app \
  -name "*.py" | head -50 && echo "---" && \
find /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src \
  -name "*.ts" -o -name "*.tsx" | head -30
```

```bash
cat /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/config.py
```

```bash
cat /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/middleware.py 2>/dev/null || \
cat /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/main.py
```

---

## PASO 2 — OWASP Top 10 (2021)

### A01: Broken Access Control
Busca endpoints sin autenticación, rutas que deberían ser privadas:
```bash
grep -rn "@router\.\(get\|post\|put\|delete\|patch\)" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/api/ \
  | grep -v "Depends\|auth\|token\|login\|health" | head -30
```

```bash
grep -rn "PUBLIC_PATHS\|whitelist\|no_auth\|skip_auth" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ | head -20
```

### A02: Cryptographic Failures
Busca algoritmos débiles, secretos en claro, hashing inseguro:
```bash
grep -rn \
  -e "md5\|sha1\|DES\|RC4\|ECB" \
  -e "hashlib\.md5\|hashlib\.sha1" \
  -e "algorithm.*HS256\|algorithm.*RS256" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ | head -20
```

```bash
grep -rn \
  -e "SECRET_KEY\s*=\s*['\"][^'\"${}]" \
  -e "password\s*=\s*['\"][^'\"${}]" \
  -e "api_key\s*=\s*['\"][^'\"${}]" \
  --include="*.py" --include="*.ts" --include="*.env*" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/ \
  --exclude-dir=".git" --exclude-dir="__pycache__" 2>/dev/null | head -20
```

### A03: Injection (SQL, Command, SSTI)
Busca construcción dinámica de SQL, ejecución de comandos sin sanitización:
```bash
grep -rn \
  -e "f\"SELECT\|f'SELECT\|format.*SELECT" \
  -e "execute(f\"\|execute(f'" \
  -e "text(f\"\|text(f'" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ | head -20
```

```bash
grep -rn \
  -e "subprocess\|os\.system\|os\.popen" \
  -e "shell=True" \
  -e "create_subprocess_shell" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ | head -20
```

### A04: Insecure Design — Scope enforcement
```bash
grep -rn "_validate_scope\|validate_scope_from_db" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ | head -20
```

```bash
grep -rn "run\|execute\|scan" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/recon/ \
  | grep -v "_validate_scope\|#" | head -20
```

### A05: Security Misconfiguration
```bash
grep -rn \
  -e "DEBUG\s*=\s*True" \
  -e "debug=True" \
  -e "allow_origins.*\*" \
  -e "CORS.*allow_all\|CORSMiddleware" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ | head -20
```

```bash
cat /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/.env 2>/dev/null \
  | grep -v "^#\|^$" | sed 's/=.*/=<HIDDEN>/' || echo ".env no accesible (OK)"
```

### A06: Vulnerable & Outdated Components
```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && \
  uv run pip list --format=json 2>/dev/null | python3 -c "
import json, sys
pkgs = json.load(sys.stdin)
critical = {'sqlalchemy': '2.0', 'fastapi': '0.100', 'python-jose': '3.0', 'passlib': '1.7'}
for p in pkgs:
    n = p['name'].lower().replace('-','').replace('_','')
    for k,v in critical.items():
        if k.replace('-','').replace('_','') in n:
            print(f'  {p[\"name\"]}: {p[\"version\"]}')
" 2>/dev/null | head -20
```

### A07: Authentication Failures
```bash
grep -rn \
  -e "expire_minutes\|expire_days\|EXPIRE" \
  -e "rate_limit\|slowapi\|RateLimiter" \
  -e "refresh_token\|access_token" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ | head -20
```

### A08: Software and Data Integrity Failures
```bash
grep -rn \
  -e "verify=False\|ssl_verify=False\|check_hostname=False" \
  -e "pickle\.loads\|yaml\.load(" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ | head -15
```

### A09: Security Logging & Monitoring Failures
```bash
grep -rn \
  -e "AgentLog\|agent_log\|log_level" \
  -e "logger\.\(warning\|error\|critical\)" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ | wc -l && \
grep -rn "password\|token\|secret" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ \
  --include="*.py" | grep "logger\." | head -10
```

### A10: Server-Side Request Forgery (SSRF)
Busca llamadas HTTP que usen input del usuario directamente:
```bash
grep -rn \
  -e "httpx\.\|aiohttp\.\|requests\." \
  -e "AsyncClient\|ClientSession" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ | head -20
```

---

## PASO 3 — MITRE ATT&CK (para herramientas de pentesting)

### T1552 — Unsecured Credentials
```bash
git -C /home/anderson/Documentos/programas\ personales/SysMho_Hunter \
  log --all --full-history -- "*.env" "*.key" "*.pem" 2>/dev/null | head -10 && \
grep -rn "ander123\|password123\|admin123\|changeme" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src/ \
  --include="*.py" --include="*.ts" --include="*.tsx" 2>/dev/null | head -10
```

### T1059 — Command & Scripting Interpreter (sanitización de argumentos)
```bash
grep -rn "target\|url\|domain" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/recon/tools/ \
  --include="*.py" | grep "f\"\|f'" | head -20
```

### T1190 — Exploit Public-Facing Application (input validation)
```bash
grep -rn "BaseModel\|validator\|field_validator\|model_validator" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/schemas/ \
  --include="*.py" | head -20
```

### T1078 — Valid Accounts (JWT handling)
```bash
cat /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/services/auth_service.py \
  | grep -A3 "def create_tokens\|def authenticate\|def verify"
```

---

## PASO 4 — CWE Top 25 Spot Checks

```bash
# CWE-89 SQL Injection + CWE-78 OS Command Injection
grep -rn "shell=True\|os\.system\|os\.popen\|subprocess\.Popen.*shell" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ \
  --include="*.py" | head -10

# CWE-22 Path Traversal
grep -rn \
  -e "open(.*request\.\|open(.*user_input\|open(.*path" \
  -e "\.\.\/" \
  --include="*.py" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ | head -10

# CWE-352 CSRF — WebSocket auth
grep -rn "token.*query\|query.*token\|?token=" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ \
  --include="*.py" | head -10
```

---

## PASO 5 — SAST con Bandit

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && \
  uv run bandit -r app/ -ll --format text 2>&1 | tail -40
```

---

## PASO 6 — Frontend Security (XSS, IDOR, Exposed Secrets)

```bash
# dangerouslySetInnerHTML (XSS)
grep -rn "dangerouslySetInnerHTML\|innerHTML\|eval(" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src/ \
  --include="*.tsx" --include="*.ts" | head -15

# IDOR — IDs expuestos sin validación
grep -rn "params\.\|useParams\|searchParams" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src/ \
  --include="*.tsx" | head -15

# Secrets hardcodeados en frontend
grep -rn \
  -e "const.*API_KEY\s*=\s*['\"]" \
  -e "const.*SECRET\s*=\s*['\"]" \
  -e "const.*TOKEN\s*=\s*['\"]" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src/ | head -10
```

---

## PASO 7 — Pending Actions Enforcement (crítico para pentesting)

```bash
grep -rn "risk_level.*high\|risk_level.*critical\|pending_actions" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ \
  --include="*.py" | grep -v "test_\|\.pyc" | head -20
```

```bash
grep -rn "await_approval\|_request_tool_approval" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/app/ \
  --include="*.py" | head -15
```

---

## SÍNTESIS FINAL

Con todos los resultados anteriores, genera un reporte estructurado:

```
╔══════════════════════════════════════════════════════════════╗
║        SYSMHO HUNTER — SECURITY AUDIT REPORT                ║
║        OWASP Top 10 | MITRE ATT&CK | CWE Top 25            ║
╚══════════════════════════════════════════════════════════════╝

SCORE GLOBAL: [0-100]

┌─────────────────────────────────────────────────────────────┐
│ OWASP Top 10 (2021)                                         │
├────────────────────────┬────────────┬───────────────────────┤
│ Control                │ Estado     │ Notas                 │
├────────────────────────┼────────────┼───────────────────────┤
│ A01 - Access Control   │ ✅/⚠️/❌  │                       │
│ A02 - Crypto           │ ✅/⚠️/❌  │                       │
│ A03 - Injection        │ ✅/⚠️/❌  │                       │
│ A04 - Insecure Design  │ ✅/⚠️/❌  │                       │
│ A05 - Misconfiguration │ ✅/⚠️/❌  │                       │
│ A06 - Outdated Deps    │ ✅/⚠️/❌  │                       │
│ A07 - Auth Failures    │ ✅/⚠️/❌  │                       │
│ A08 - Integrity        │ ✅/⚠️/❌  │                       │
│ A09 - Logging          │ ✅/⚠️/❌  │                       │
│ A10 - SSRF             │ ✅/⚠️/❌  │                       │
└────────────────────────┴────────────┴───────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MITRE ATT&CK (Pentesting Tool Specific)                     │
├────────────────────────┬────────────┬───────────────────────┤
│ T1552 Credentials      │ ✅/⚠️/❌  │                       │
│ T1059 Cmd Injection    │ ✅/⚠️/❌  │                       │
│ T1190 Input Validation │ ✅/⚠️/❌  │                       │
│ T1078 Auth/JWT         │ ✅/⚠️/❌  │                       │
└────────────────────────┴────────────┴───────────────────────┘

HALLAZGOS CRÍTICOS:
  [Lista de vulnerabilidades CRÍTICAS encontradas]

HALLAZGOS MEDIOS:
  [Lista de vulnerabilidades MEDIAS]

RECOMENDACIONES:
  [Acciones concretas para remediar, en orden de prioridad]

VEREDICTO:
  🟢 LISTO PARA OPERAR  /  🟡 OPERAR CON PRECAUCIÓN  /  🔴 NO OPERAR
```
