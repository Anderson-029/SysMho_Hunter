---
name: hunter-config
description: Ver y modificar la configuración del agente en caliente — umbrales del cerebro híbrido, timeouts de herramientas, fases de recon, modo activo. Úsalo cuando quieras ajustar el comportamiento sin reiniciar el backend.
---

Ejecuta los diagnósticos de configuración del agente:

**1. Configuración completa del agente (agent_config):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  key,
  value::text,
  description,
  to_char(updated_at, 'DD/MM/YYYY HH24:MI') as actualizado
FROM agent_config
ORDER BY key;
" 2>/dev/null || echo "BD no disponible"
```

**2. Verificar config activa via API:**
```bash
curl -s http://localhost:8000/health 2>/dev/null | python3 -m json.tool || echo "Backend offline"
```

Presenta los resultados agrupados por prefijo:

**Cerebro (brain.*)**
- `brain.ml_confidence_threshold` — Umbral ML (default: 0.85). Si baja → más trabajo a Ollama.
- `brain.local_llm_confidence_threshold` — Umbral Ollama (default: 0.70). Si baja → más trabajo a Cloud.
- `brain.active_brain` — auto | ml | local | cloud

**Reconocimiento (recon.*)**
- `recon.max_concurrent_tools` — Herramientas en paralelo (default: 5)
- `recon.default_timeout` — Timeout por herramienta en segundos (default: 300)
- `recon.default_phases` — Fases activas por defecto

**Scope y Seguridad (scope.*)**
- `scope.strict_mode` — Si true, bloquea todo target no en scopes table

**Acciones (actions.*)**
- `actions.auto_approve_low_risk` — Si true, aprueba automáticamente risk_level=low

**Reportes (report.*)**
- `report.h1_min_quality_score` — Score mínimo para marcar reporte como listo (default: 7)

---

**Para modificar un valor en caliente (sin reiniciar backend):**

```bash
# Ejemplo: bajar umbral ML para forzar más uso de Ollama
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -c "
UPDATE agent_config
SET value = '0.75', updated_at = NOW()
WHERE key = 'brain.ml_confidence_threshold';
"
```

```bash
# Ejemplo: aumentar herramientas paralelas
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -c "
UPDATE agent_config
SET value = '8', updated_at = NOW()
WHERE key = 'recon.max_concurrent_tools';
"
```

Los cambios aplican en la **siguiente llamada al BrainRouter** — no requiere restart.
