---
name: hunter-ui-audit
description: Auditoría del frontend — componentes existentes, dependencias instaladas vs recomendadas, score UI Readiness 0-10. Úsalo antes de planificar un upgrade.
---

Inventario de componentes:

```bash
ls -la /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src/components/ && \
wc -l /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/src/components/*.tsx 2>/dev/null
```

Dependencias instaladas vs recomendadas:

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend && \
node -e "
const pkg = require('./package.json');
const deps = {...pkg.dependencies, ...pkg.devDependencies};
['recharts','@tanstack/react-table','framer-motion','lucide-react',
 'sonner','@tanstack/react-virtual','date-fns'].forEach(d =>
  console.log(deps[d] ? '✅ '+d+' '+deps[d] : '❌ FALTA: '+d));
"
```

Score UI Readiness: recharts=+2, @tanstack/react-table=+2, framer-motion=+1, lucide-react=+1, sonner=+1, @tanstack/react-virtual=+2, date-fns=+1.

Si score < 10, ejecuta: `/hunter-ui-upgrade`.
