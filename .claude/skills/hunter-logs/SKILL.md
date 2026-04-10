---
name: hunter-logs
description: Últimos logs del sistema — muestra agent_logs agrupados por nivel (ERROR/WARNING/INFO), filtra por scan activo si hay uno corriendo. Úsalo para debugging cuando un scan falla o el comportamiento es inesperado.
---

Ejecuta el análisis de logs del sistema:

**1. Verificar si hay scan activo:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT id, scan_type, status, phase, started_at
FROM scans
WHERE status IN ('running', 'pending')
ORDER BY started_at DESC
LIMIT 1;
" 2>/dev/null
```

**2. Últimos 50 logs (todos los componentes):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  to_char(created_at, 'HH24:MI:SS') as hora,
  log_level,
  component,
  message
FROM agent_logs
ORDER BY created_at DESC
LIMIT 50;
" 2>/dev/null || echo "BD no disponible"
```

**3. Errores y warnings de las últimas 2 horas:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  to_char(created_at, 'HH24:MI:SS') as hora,
  log_level,
  component,
  message
FROM agent_logs
WHERE log_level IN ('ERROR', 'WARNING', 'CRITICAL')
  AND created_at > NOW() - INTERVAL '2 hours'
ORDER BY created_at DESC
LIMIT 30;
" 2>/dev/null || echo "Sin errores recientes"
```

**4. Logs por componente (conteo últimas 24h):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  component,
  log_level,
  COUNT(*) as total
FROM agent_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY component, log_level
ORDER BY component, log_level;
" 2>/dev/null
```

Presenta los resultados con:
- 🔴 ERROR / CRITICAL — requieren atención inmediata
- 🟡 WARNING — revisar si son esperados
- 🟢 INFO / DEBUG — flujo normal

Si hay un scan activo → mostrar sus logs específicos al inicio.
Si hay errores recurrentes del mismo componente → señalarlo con ⚠️ y sugerir el módulo a revisar:
- `ReconEngine` → `backend/app/recon/engine.py`
- `BrainRouter` → `backend/app/brain/router.py`
- `ScanService` → `backend/app/services/scan_service.py`
- `ToolRegistry` → `backend/app/recon/tool_registry.py`
