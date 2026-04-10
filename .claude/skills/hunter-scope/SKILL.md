---
name: hunter-scope
description: Gestión de targets y scopes autorizados — lista targets activos, sus scopes por tipo (domain/ip/cidr/url/wildcard), y violaciones recientes. Úsalo antes de lanzar un scan para confirmar que el target está autorizado.
---

Ejecuta los siguientes diagnósticos sobre targets y scopes:

**1. Targets activos:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  substring(id::text, 1, 8) as id,
  name,
  organization,
  status,
  priority,
  h1_program_slug
FROM targets
WHERE status != 'inactive'
ORDER BY priority DESC, name;
" 2>/dev/null || echo "BD no disponible"
```

**2. Scopes por target (in_scope y out_scope):**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  t.name as target,
  s.scope_type,
  s.value,
  CASE WHEN s.is_in_scope THEN 'IN SCOPE' ELSE 'OUT OF SCOPE' END as scope_status
FROM scopes s
JOIN targets t ON s.target_id = t.id
WHERE t.status != 'inactive'
ORDER BY t.name, s.is_in_scope DESC, s.scope_type;
" 2>/dev/null || echo "BD no disponible"
```

**3. Últimas violaciones de scope detectadas:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  component,
  message,
  to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as when
FROM agent_logs
WHERE message ILIKE '%scope%' OR message ILIKE '%ScopeViolation%'
ORDER BY created_at DESC
LIMIT 10;
" 2>/dev/null || echo "Sin violaciones registradas o BD no disponible"
```

Presenta los resultados con formato:
- ✅ IN SCOPE → autorizado para scan
- ❌ OUT OF SCOPE → NO ejecutar herramientas
- Incluye resumen: "X targets activos, Y scopes in-scope disponibles"
- Si no hay targets → recordar: `POST /api/v1/targets` para agregar uno
