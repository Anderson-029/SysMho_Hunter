---
name: hunter-scan
description: Vista táctica de escaneos — scans activos, fase del pipeline, tools corriendo y últimos completados. Úsalo cuando revises estado de operaciones en curso.
---

Consulta el estado de los scans activos y recientes:

```bash
PGPASSWORD=$DB_PASSWORD psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -c "
-- Scans activos
SELECT s.id, s.status, s.phase, s.scan_type, t.name as target,
       s.started_at, NOW() - s.started_at as duracion
FROM scans s JOIN targets t ON s.target_id = t.id
WHERE s.status IN ('running','pending')
ORDER BY s.started_at DESC;

-- Tasks corriendo ahora
SELECT st.tool_name, st.status, st.target_value,
       NOW() - st.started_at as duracion
FROM scan_tasks st
JOIN scans s ON st.scan_id = s.id
WHERE s.status = 'running' AND st.status = 'running';

-- Últimos 5 completados
SELECT s.id, s.status, s.scan_type, t.name as target,
       s.started_at, s.completed_at,
       s.completed_at - s.started_at as duracion_total
FROM scans s JOIN targets t ON s.target_id = t.id
WHERE s.status IN ('completed','failed')
ORDER BY s.completed_at DESC LIMIT 5;
"
```
