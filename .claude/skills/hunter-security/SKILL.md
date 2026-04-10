---
name: hunter-security
description: Escaneo de seguridad del código — bandit SAST, secretos hardcodeados, .env en git, permisos de scripts. Úsalo antes de hacer push.
---

Ejecuta 3 checks de seguridad:

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && \
  (uv run bandit --version &>/dev/null || uv pip install bandit) && \
  uv run bandit -r app/ -ll --format text 2>&1 | head -80
```

```bash
grep -rn \
  -e 'password\s*=\s*["'"'"'][^"'"'"'${}]' \
  -e 'api_key\s*=\s*["'"'"'][^"'"'"'${}]' \
  -e 'secret\s*=\s*["'"'"'][^"'"'"'${}]' \
  -e 'token\s*=\s*["'"'"'][^"'"'"'${}]' \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  --exclude-dir=".git" --exclude-dir="node_modules" \
  --exclude-dir="__pycache__" \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend/ \
  /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src/ 2>/dev/null \
  || echo "OK — no se encontraron secretos hardcodeados"
```

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter && \
git ls-files | grep '\.env$' && echo "ALERTA: .env en git tracking" || echo "OK — .env seguro"
```

Reporta PASS/WARN/FAIL por cada check.
