---
name: hunter-report
description: Genera y previsualiza el reporte HackerOne del último scan completado. Úsalo antes de submitear un reporte para verificar calidad y estructura.
---

```bash
PGPASSWORD=$DB_PASSWORD psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
-- Último reporte generado
SELECT r.id, r.title, r.status, t.name as target,
       r.created_at, length(r.h1_format_md) as chars_md
FROM reports r JOIN targets t ON r.target_id = t.id
ORDER BY r.created_at DESC LIMIT 1;
" 2>/dev/null

# Previsualizar el markdown del último reporte
PGPASSWORD=$DB_PASSWORD psql -h ${DB_HOST:-127.0.0.1} -U ${DB_USER:-postgres} -d ${DB_NAME:-sysmho_hunter} -t -c "
SELECT h1_format_md FROM reports ORDER BY created_at DESC LIMIT 1;
" 2>/dev/null | head -60

echo ""
echo "=== CHECKLIST CALIDAD H1 ==="
# Verificar estructura requerida por HackerOne via API
curl -s http://localhost:8000/api/v1/reports/latest/quality-check 2>/dev/null || echo "Backend no disponible para check de calidad"
```
