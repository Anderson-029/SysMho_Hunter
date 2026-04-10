---
name: hunter-ui-upgrade
description: Instala dependencias pro del frontend — recharts, tanstack table, framer-motion, lucide-react, sonner, virtual scroll, date-fns. Úsalo después de /hunter-ui-audit cuando score < 10.
---

Verificar que el frontend tiene node_modules:

```bash
ls /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend/node_modules/.package-lock.json 2>/dev/null || (cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend && npm install)
```

Instalar dependencias pro:

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend && npm install \
  recharts \
  @tanstack/react-table \
  framer-motion \
  lucide-react \
  sonner \
  @tanstack/react-virtual \
  date-fns
```

Verificar instalación exitosa:

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend && node -e "
const pkg = require('./package.json');
const deps = pkg.dependencies;
let ok=true;
['recharts','@tanstack/react-table','framer-motion','lucide-react',
 'sonner','@tanstack/react-virtual','date-fns'].forEach(d => {
  if(deps[d]) console.log('✅ '+d+' '+deps[d]);
  else { console.log('❌ FALLO: '+d); ok=false; }
});
process.exit(ok?0:1);
"
```

Test de compilación TypeScript:

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/frontend && npx tsc --noEmit 2>&1 | head -30 || echo "WARN: hay errores TS — revisar antes de continuar"
```

Si `npm install` falla con ERESOLVE (conflicto React 19): usar `npm install --legacy-peer-deps`.
