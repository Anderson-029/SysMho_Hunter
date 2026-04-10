---
name: hunter-stats
description: Dashboard estadístico completo — total scans por estado, findings por severidad, herramientas más usadas, tasa de éxito, tokens cloud consumidos y distribución de uso del cerebro por nivel. Vista ejecutiva del rendimiento de SysMho Hunter.
---

Ejecuta el dashboard estadístico en paralelo:

**1. Resumen global de scans:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  status,
  COUNT(*) as total,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) as pct
FROM scans
GROUP BY status
ORDER BY total DESC;
" 2>/dev/null || echo "BD no disponible"
```

**2. Findings por severidad:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  severity,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE status = 'new') as nuevos,
  COUNT(*) FILTER (WHERE status = 'confirmed') as confirmados,
  COUNT(*) FILTER (WHERE status = 'reported') as reportados
FROM findings
GROUP BY severity
ORDER BY
  CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END;
" 2>/dev/null
```

**3. Findings por tipo de vulnerabilidad (top 10):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  vuln_type,
  COUNT(*) as total,
  ROUND(AVG(cvss_score), 2) as cvss_promedio
FROM findings
WHERE vuln_type IS NOT NULL
GROUP BY vuln_type
ORDER BY total DESC
LIMIT 10;
" 2>/dev/null
```

**4. Herramientas más usadas (éxito vs fallo):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  tool_name,
  COUNT(*) as ejecuciones,
  COUNT(*) FILTER (WHERE status = 'completed') as exitosas,
  COUNT(*) FILTER (WHERE status = 'failed') as fallidas,
  ROUND(AVG(EXTRACT(EPOCH FROM (updated_at - created_at))), 0) as avg_segundos
FROM scan_tasks
WHERE tool_name IS NOT NULL
GROUP BY tool_name
ORDER BY ejecuciones DESC
LIMIT 15;
" 2>/dev/null
```

**5. Uso del cerebro híbrido (distribución por nivel, últimas 24h):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  brain_level,
  model_used,
  COUNT(*) as decisiones,
  ROUND(AVG(confidence), 3) as confianza_promedio,
  ROUND(AVG(latency_ms), 0) as latencia_ms_promedio,
  COALESCE(SUM(tokens_used), 0) as tokens_totales
FROM brain_reasoning
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY brain_level, model_used
ORDER BY brain_level, decisiones DESC;
" 2>/dev/null
```

**6. Tokens cloud (costo estimado últimas 24h):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  model_used,
  SUM(tokens_used) as tokens_totales,
  COUNT(*) as llamadas
FROM brain_reasoning
WHERE brain_level = 3
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY model_used;
" 2>/dev/null || echo "Sin llamadas cloud en las últimas 24h"
```

**7. Reportes HackerOne generados:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  status,
  COUNT(*) as total,
  COALESCE(SUM(bounty_amount), 0) as bounty_total_usd
FROM reports
GROUP BY status;
" 2>/dev/null
```

Presenta un dashboard con secciones:

## Resumen Ejecutivo
- Total scans | Tasa de éxito | Findings totales

## Severidad de Findings
- Tabla crítico/alto/medio/bajo con nuevos/confirmados/reportados

## Arsenal
- Top 5 herramientas más efectivas (tasa éxito)

## Cerebro Híbrido (últimas 24h)
- Nivel 1 (ML): X decisiones, confianza Y
- Nivel 2 (Ollama): X decisiones, latencia Yms
- Nivel 3 (Cloud): X llamadas, Z tokens totales

## HackerOne
- Reportes draft/ready, bounty acumulado si aplica
