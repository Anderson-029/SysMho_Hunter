---
name: hunter-brain
description: Estado del cerebro híbrido — nivel activo, confianza media por nivel, últimas decisiones de razonamiento y costo de tokens cloud. Úsalo cuando evalúes el rendimiento del cerebro.
---

```bash
# Estado de Ollama
echo "=== OLLAMA ==="
curl -s http://localhost:11434/api/tags | python3 -c "
import json,sys
d=json.load(sys.stdin)
for m in d.get('models',[]):
    print(f'  Modelo: {m[\"name\"]} ({m[\"size\"]//1024//1024} MB)')
" 2>/dev/null || echo "  Ollama OFFLINE"

# Estadísticas del cerebro desde BD
PGPASSWORD=$DB_PASSWORD psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -c "
-- Uso por nivel (últimas 24h)
SELECT brain_level, model_used, COUNT(*) as llamadas,
       ROUND(AVG(confidence)::numeric, 3) as confianza_media,
       ROUND(AVG(latency_ms)::numeric) as latencia_media_ms,
       SUM(tokens_used) as tokens_totales
FROM brain_reasoning
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY brain_level, model_used
ORDER BY brain_level;

-- Últimas 5 decisiones
SELECT task_type, brain_level, model_used, confidence,
       latency_ms, reasoning_text, created_at
FROM brain_reasoning
ORDER BY created_at DESC LIMIT 5;

-- Config activa
SELECT key, value FROM agent_config
WHERE key LIKE 'brain.%' ORDER BY key;
"
```
