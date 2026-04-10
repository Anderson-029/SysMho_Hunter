---
name: hunter-performance
description: Análisis de performance y optimización — latencia del cerebro por nivel, herramientas lentas, cuello de botella del pipeline, costo cloud y recomendaciones concretas de mejora. Úsalo cuando el sistema sea lento, los scans tarden demasiado, o quieras optimizar costos de cloud.
---

Ejecuta los 5 bloques de análisis y luego genera recomendaciones automáticas basadas en los datos.

---

**BLOQUE 1 — Resumen Ejecutivo del Pipeline**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  COUNT(*) as total_scans,
  COUNT(*) FILTER (WHERE status='completed') as exitosos,
  COUNT(*) FILTER (WHERE status='failed') as fallidos,
  COUNT(*) FILTER (WHERE status IN ('running','pending')) as en_curso,
  ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60), 1) as duracion_media_min,
  ROUND(MIN(EXTRACT(EPOCH FROM (completed_at - started_at))/60), 1) as duracion_minima_min,
  ROUND(MAX(EXTRACT(EPOCH FROM (completed_at - started_at))/60), 1) as duracion_maxima_min
FROM scans
WHERE completed_at IS NOT NULL AND started_at IS NOT NULL;
" 2>/dev/null || echo "Sin datos de scans completados"
```

---

**BLOQUE 2 — Cerebro Híbrido: Latencia y Confianza por Nivel**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
-- Métricas por nivel (últimos 7 días)
SELECT
  brain_level,
  model_used,
  COUNT(*) as decisiones,
  ROUND(AVG(confidence), 3) as confianza_media,
  ROUND(AVG(latency_ms), 0) as latencia_media_ms,
  ROUND(MAX(latency_ms), 0) as latencia_max_ms,
  COALESCE(SUM(tokens_used), 0) as tokens_totales,
  COUNT(*) FILTER (WHERE confidence < 0.70) as decisiones_baja_conf
FROM brain_reasoning
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY brain_level, model_used
ORDER BY brain_level;
" 2>/dev/null || echo "Sin decisiones del cerebro en los últimos 7 días"
```

```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
-- Escalamiento por tipo de tarea (cuál fuerza más uso de cloud)
SELECT
  task_type,
  COUNT(*) as total,
  ROUND(AVG(brain_level), 2) as nivel_promedio,
  ROUND(AVG(confidence), 3) as confianza_promedio,
  COUNT(*) FILTER (WHERE brain_level=1) as nivel1_ml,
  COUNT(*) FILTER (WHERE brain_level=2) as nivel2_ollama,
  COUNT(*) FILTER (WHERE brain_level=3) as nivel3_cloud
FROM brain_reasoning
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY task_type
ORDER BY nivel_promedio DESC;
" 2>/dev/null
```

---

**BLOQUE 3 — Herramientas Lentas y con Fallos**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  tool_name,
  COUNT(*) as ejecuciones,
  COUNT(*) FILTER (WHERE status='completed') as exitosas,
  COUNT(*) FILTER (WHERE status='failed') as fallidas,
  ROUND(COUNT(*) FILTER (WHERE status='failed') * 100.0 / NULLIF(COUNT(*), 0), 1) as pct_fallo,
  ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - started_at))), 0) as duracion_media_seg,
  ROUND(MAX(EXTRACT(EPOCH FROM (completed_at - started_at))), 0) as duracion_max_seg
FROM scan_tasks
WHERE started_at IS NOT NULL AND completed_at IS NOT NULL
GROUP BY tool_name
ORDER BY duracion_media_seg DESC NULLS LAST
LIMIT 15;
" 2>/dev/null || echo "Sin datos de herramientas"
```

---

**BLOQUE 4 — Cuello de Botella por Fase del Pipeline**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  CASE
    WHEN tool_name IN ('subfinder','amass') THEN '1_subdomain_enum'
    WHEN tool_name IN ('nmap','masscan') THEN '2_port_scan'
    WHEN tool_name IN ('whatweb','wafw00f','httprobe','eyewitness') THEN '3_web_fingerprint'
    WHEN tool_name IN ('hakrawler','gau','waybackurls') THEN '4_crawl'
    WHEN tool_name IN ('nuclei','nikto','ffuf','feroxbuster','gobuster','wfuzz','dalfox') THEN '5_vuln_scan'
    WHEN tool_name IN ('sqlmap') THEN '6_exploit'
    ELSE 'otro'
  END as fase,
  COUNT(*) as total_ejecuciones,
  ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - started_at))), 0) as avg_seg_por_tool,
  ROUND(SUM(EXTRACT(EPOCH FROM (completed_at - started_at))), 0) as tiempo_total_seg
FROM scan_tasks
WHERE started_at IS NOT NULL AND completed_at IS NOT NULL
GROUP BY fase
ORDER BY fase;
" 2>/dev/null || echo "Sin datos de fases"
```

---

**BLOQUE 5 — Costo Cloud y Eficiencia de Tokens (últimos 30 días)**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  model_used,
  COUNT(*) as llamadas,
  COALESCE(SUM(tokens_used), 0) as tokens_totales,
  ROUND(AVG(tokens_used), 0) as tokens_por_llamada,
  ROUND(AVG(confidence), 3) as confianza_media,
  ROUND(AVG(latency_ms), 0) as latencia_media_ms,
  -- Estimación orientativa de costo (USD)
  -- Gemini 2.0 Flash: ~$0.075/1M tokens | Claude Haiku: ~$0.25/1M tokens
  CASE
    WHEN model_used ILIKE '%gemini%'
      THEN ROUND(COALESCE(SUM(tokens_used),0) * 0.000000075, 5)
    WHEN model_used ILIKE '%claude%' OR model_used ILIKE '%haiku%'
      THEN ROUND(COALESCE(SUM(tokens_used),0) * 0.00000025, 5)
    ELSE 0
  END as costo_estimado_usd
FROM brain_reasoning
WHERE brain_level = 3
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY model_used;
" 2>/dev/null || echo "Sin llamadas cloud en los últimos 30 días"
```

---

**BLOQUE 6 — Recomendaciones Automáticas**

Basándote en los datos de los bloques anteriores, analiza las siguientes condiciones y presenta las recomendaciones que apliquen:

**Condiciones a evaluar:**

1. Si el nivel promedio del cerebro (bloque 2) es **> 2.0** en últimas 24h:
   - **Problema:** El sistema escala demasiado a cloud (costo elevado)
   - **Por qué pasa:** Confianza ML baja o Ollama offline
   - **Cómo mejorarlo:** Verificar Ollama con `/hunter-brain`. Si está caído: `ollama serve`. Si la confianza ML es baja → reentrenar modelos en `ml/`
   - **Impacto:** Reducir llamadas cloud = menor latencia y menor costo

2. Si la confianza media del Nivel 1 (ML) es **< 0.75**:
   - **Problema:** Modelos scikit-learn con datos insuficientes o desactualizados
   - **Por qué pasa:** Pocos findings históricos para entrenar, o distribución de datos sesgada
   - **Cómo mejorarlo:** Agregar más findings etiquetados y reentrenar: `cd ml && uv run python train.py`
   - **Impacto:** Más decisiones en Nivel 1 (<10ms) → pipeline más rápido y sin costo cloud

3. Si alguna herramienta tiene **pct_fallo > 30%** (bloque 3):
   - **Problema:** Herramienta rota, mal instalada o con timeout insuficiente
   - **Por qué pasa:** Binary no en PATH, versión incompatible, o target rechaza las peticiones
   - **Cómo mejorarlo:** `/hunter-recon` para verificar instalación. Si timeout: aumentar en `agent_config`: `UPDATE agent_config SET value='600' WHERE key='recon.default_timeout';`
   - **Impacto:** Elimina scan_tasks fallidas que detienen el pipeline

4. Si la duración media del pipeline es **> 30 minutos** (bloque 1):
   - **Problema:** Pipeline muy lento para uso iterativo
   - **Por qué pasa:** Muchas fases activas, herramientas lentas (amass, masscan), concurrencia baja
   - **Cómo mejorarlo:** Aumentar concurrencia: `UPDATE agent_config SET value='8' WHERE key='recon.max_concurrent_tools';`. O desactivar fases lentas en `recon.default_phases`
   - **Impacto:** Reducción del 30-50% en tiempo total de scan

5. Si `duracion_max_seg > 500` para alguna tool (bloque 3):
   - **Problema:** Herramienta supera el timeout → bloquea el pipeline
   - **Por qué pasa:** Target lento, red congestionada, o herramienta sin límite interno
   - **Cómo mejorarlo:** Revisar el `default_timeout` en `backend/app/recon/tools/<tool>.py` y ajustar a 400s máximo
   - **Impacto:** Evita que un solo tool congele todo el scan

6. Si tokens cloud totales **> 50,000 en 7 días** (bloque 5):
   - **Problema:** Gasto cloud elevado, posiblemente innecesario
   - **Por qué pasa:** Ollama offline frecuentemente o umbrales de confianza muy altos
   - **Cómo mejorarlo:** Bajar umbral Ollama: `UPDATE agent_config SET value='0.60' WHERE key='brain.local_llm_confidence_threshold';`
   - **Impacto:** Más trabajo resuelto por Ollama local (gratis) en lugar de cloud (de pago)

---

Presenta el reporte final con secciones numeradas y usa:
- 🔴 **CRÍTICO** — degradación grave del sistema
- 🟠 **ALTO** — impacto significativo en performance o costo
- 🟡 **MEDIO** — optimización recomendable
- 🟢 **OK** — métrica dentro de rango esperado

Termina con una sección **"Top 3 acciones recomendadas"** con los comandos listos para ejecutar.
