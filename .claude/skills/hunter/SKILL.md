---
name: hunter
description: Panel diagnóstico maestro — verifica procesos activos (backend, ollama, postgresql), estado de BD, scans recientes y pending_actions. Úsalo cuando necesites una vista rápida del estado completo del sistema.
---

Ejecuta los siguientes diagnósticos en paralelo y presenta un resumen estructurado:

**1. Procesos activos:**
```bash
pgrep -a uvicorn | head -3
pgrep -a ollama | head -2
systemctl is-active postgresql 2>/dev/null || pg_isready -h 127.0.0.1 -p 5432
```

**2. Health del backend:**
```bash
curl -s http://localhost:8000/health 2>/dev/null || echo "Backend offline"
```

**3. Estado de Ollama:**
```bash
curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'  - {m[\"name\"]}') for m in d.get('models',[])]" 2>/dev/null || echo "Ollama offline"
```

**4. Base de datos — scans recientes y pending_actions:**
```bash
PGPASSWORD=$DB_PASSWORD psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT 'SCANS RECIENTES' as info;
SELECT id, status, scan_type, started_at FROM scans ORDER BY started_at DESC LIMIT 5;
SELECT 'PENDING ACTIONS' as info;
SELECT id, action_type, risk_level, status FROM pending_actions WHERE status='pending' LIMIT 10;
" 2>/dev/null || echo "BD no disponible"
```

Presenta los resultados en formato claro con estado: ✅ OK / ⚠️ Warning / ❌ Error
