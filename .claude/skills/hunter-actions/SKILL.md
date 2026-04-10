---
name: hunter-actions
description: Gestión de pending_actions — vista de operaciones bloqueadas esperando aprobación humana (risk_level high/critical). Muestra payload, herramienta que la generó y tiempo pendiente. Úsalo cuando un scan se detenga por acciones de alto riesgo.
---

Ejecuta los diagnósticos de pending_actions:

**1. Acciones pendientes de aprobación:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  substring(pa.id::text, 1, 8) as id,
  pa.action_type,
  pa.risk_level,
  pa.status,
  substring(t.name, 1, 30) as target,
  pa.description,
  to_char(pa.created_at, 'DD/MM HH24:MI') as creado,
  EXTRACT(EPOCH FROM (NOW() - pa.created_at))::int / 60 as mins_esperando
FROM pending_actions pa
LEFT JOIN targets t ON pa.target_id = t.id
WHERE pa.status = 'pending'
ORDER BY
  CASE pa.risk_level WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
  pa.created_at ASC;
" 2>/dev/null || echo "BD no disponible"
```

**2. Payload de acciones críticas (últimas 3):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  substring(id::text, 1, 8) as id,
  action_type,
  risk_level,
  payload::text
FROM pending_actions
WHERE status = 'pending' AND risk_level IN ('critical', 'high')
ORDER BY created_at ASC
LIMIT 3;
" 2>/dev/null || echo "Sin acciones críticas pendientes"
```

**3. Historial reciente (aprobadas/rechazadas hoy):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  action_type,
  risk_level,
  status,
  reviewed_by,
  to_char(updated_at, 'DD/MM HH24:MI') as revisado
FROM pending_actions
WHERE status IN ('approved', 'rejected', 'executed')
  AND updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC
LIMIT 10;
" 2>/dev/null || echo "Sin actividad reciente"
```

Presenta los resultados con:
- 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM por cada acción pendiente
- Tiempo de espera en minutos
- Instrucciones para aprobar/rechazar:

**Para aprobar/rechazar una acción (reemplaza {ID} con el id completo):**
```bash
curl -s -X POST http://localhost:8000/api/v1/actions/{ID}/review \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "comment": "Aprobado manualmente"}' | python3 -m json.tool
```

```bash
curl -s -X POST http://localhost:8000/api/v1/actions/{ID}/review \
  -H "Content-Type: application/json" \
  -d '{"decision": "rejected", "comment": "Rechazado — fuera de scope"}' | python3 -m json.tool
```

Si no hay acciones pendientes → mostrar "✅ Sin acciones bloqueadas. El pipeline puede continuar."
