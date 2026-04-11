---
name: hunter-h1
description: Dashboard de integración HackerOne — estado de conexión, perfil del hacker (reputation/signal/impact), programas activos sincronizados, últimos reportes enviados y su estado. Úsalo para verificar la conexión con H1 y gestionar el flujo de reportes.
---

Ejecuta el diagnóstico completo de la integración HackerOne:

**1. Estado de conexión y perfil:**
```bash
curl -s http://localhost:8000/api/v1/h1/profile 2>/dev/null | python3 -m json.tool || echo "Backend offline o credenciales no configuradas"
```

**2. Programas en los que participo:**
```bash
curl -s http://localhost:8000/api/v1/h1/programs 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
programs = d.get('programs', [])
print(f'Total programas: {len(programs)}')
for p in programs:
    bounty = '💰' if p.get('offers_bounties') else '  '
    state = p.get('submission_state', 'unknown')
    print(f'  {bounty} [{state}] {p[\"handle\"]} — {p[\"name\"]}')
" 2>/dev/null || echo "Error al obtener programas"
```

**3. Programas sincronizados en BD local:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  name,
  h1_program_slug,
  status,
  (SELECT COUNT(*) FROM scopes WHERE target_id = t.id AND is_in_scope = true) as scopes_in,
  (SELECT COUNT(*) FROM scopes WHERE target_id = t.id AND is_in_scope = false) as scopes_out
FROM targets t
WHERE h1_program_slug IS NOT NULL AND h1_program_slug != ''
ORDER BY name;
" 2>/dev/null || echo "BD no disponible"
```

**4. Últimos reportes enviados a H1:**
```bash
curl -s "http://localhost:8000/api/v1/h1/reports?per_page=10" 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
reports = d.get('reports', [])
if not reports:
    print('Sin reportes enviados a HackerOne')
else:
    print(f'Últimos {len(reports)} reportes:')
    for r in reports:
        state = r.get('state', '?')
        sev = r.get('severity', 'N/A')
        bounty = f\" 💰 \${r['bounty']}\" if r.get('bounty') else ''
        print(f\"  #{r['id']} [{state}] {sev} — {r['title'][:50]}{bounty}\")
" 2>/dev/null || echo "Error al obtener reportes"
```

**5. Reportes locales listos para submitear:**
```bash
PGPASSWORD=${DB_PASSWORD:-ander123} psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT
  substring(r.id::text, 1, 8) as id,
  r.title,
  r.status,
  r.h1_report_id,
  to_char(r.created_at, 'DD/MM/YYYY') as fecha,
  LENGTH(r.h1_format_md) as chars_md
FROM reports r
ORDER BY r.created_at DESC
LIMIT 10;
" 2>/dev/null
```

Presenta los resultados con:

## Conexión HackerOne
- ✅ Conectado / ❌ Sin configurar (agregar H1_API_TOKEN y H1_USERNAME en backend/.env)

## Mi Perfil
- Username, Reputation, Signal, Impact

## Programas (H1 vs BD local)
- Total en H1 vs sincronizados en BD

## Reportes
- Últimos enviados con estado y bounty
- Locales listos para submitear (status=ready, h1_report_id=null)

---

**Comandos operativos:**

```bash
# Sincronizar todos los programas y scopes de H1 → BD
curl -s -X POST http://localhost:8000/api/v1/h1/sync | python3 -m json.tool

# Submitear un reporte (reemplaza {REPORT_ID} con el UUID del reporte)
curl -s -X POST http://localhost:8000/api/v1/h1/reports/{REPORT_ID}/submit | python3 -m json.tool

# Ver estado de un reporte ya enviado (reemplaza {H1_ID} con el número H1)
curl -s http://localhost:8000/api/v1/h1/reports/{H1_ID}/status | python3 -m json.tool
```

**Si las credenciales no están configuradas:**
1. Obtén tu API token en: `https://hackerone.com/settings/api_token/edit`
2. Agrega a `backend/.env`:
   ```
   H1_API_TOKEN=tu_token_aqui
   H1_USERNAME=tu_username_aqui
   ```
3. Reinicia el backend: `cd backend && uv run uvicorn app.main:app --reload`
