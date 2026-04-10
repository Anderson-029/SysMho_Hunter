---
name: hunter-findings
description: Vista ofensiva de hallazgos — distribución por severidad, vulnerabilidades críticas/altas, cadenas detectadas. Úsalo cuando evalúes resultados o prepares un reporte.
---

```bash
PGPASSWORD=$DB_PASSWORD psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -c "
-- Distribución por severidad
SELECT severity, COUNT(*) as total, 
       COUNT(*) FILTER (WHERE status='new') as nuevos,
       COUNT(*) FILTER (WHERE status='confirmed') as confirmados
FROM findings
GROUP BY severity
ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END;

-- Críticos y altos recientes
SELECT f.id, f.title, f.severity, f.vuln_type, f.url, f.status,
       f.ml_severity, f.ml_confidence, t.name as target
FROM findings f JOIN targets t ON f.target_id = t.id
WHERE f.severity IN ('critical','high') AND f.status NOT IN ('not_applicable','duplicate')
ORDER BY f.discovered_at DESC LIMIT 10;
"
```
