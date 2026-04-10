---
name: hunter-ci
description: Pipeline CI local antes de commit — lint, formato, imports, .env check y health. Resultado final PASS/FAIL. Úsalo siempre antes de git commit.
---

Ejecuta el pipeline en 4 pasos secuenciales:

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && uv run ruff check app/ --output-format=concise 2>&1
```

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && uv run python -c "from app.main import app; print('OK')" 2>&1
```

```bash
curl -sf http://localhost:8000/health 2>/dev/null && echo "Backend: ONLINE" || echo "Backend: OFFLINE (informativo)"
```

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter && \
git diff --cached --name-only | grep '\.env' \
  && echo "FALLO: .env en staging — usa: git restore --staged .env" \
  || echo "OK — .env no está en staging"
```

Presenta tabla final: PASO 1-4 con PASS/FAIL y resultado final ✅ PASS o ❌ FAIL.
