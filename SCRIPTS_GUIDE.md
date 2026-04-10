# 🚀 Guía de Scripts — SysMho Hunter

## Inicio Rápido

```bash
# Iniciar TODO (PostgreSQL → Ollama → Backend → Frontend)
bash scripts/start_hunter.sh

# Detener TODO (limpia procesos, puertos, zombies)
bash scripts/stop_hunter.sh
```

---

## 📄 Qué Hace Cada Script

### `start_hunter.sh` — Inicializa el sistema completo

**Orden de arranque (lógico y secuencial):**
1. ✅ **Prerequisitos** — Verifica python3, node, psql, curl, uv instalados
2. ✅ **PostgreSQL** — Inicia BD si no está corriendo (localhost:5432)
3. ✅ **Ollama** — Inicia Ollama (localhost:11434) y descarga Llama 3.1 8B **solo si no existe**
4. ✅ **Migraciones** — Aplica schema de tablas (targets, scans, findings, etc)
5. ✅ **Backend** — Inicia FastAPI en puerto 8000 con reload automático
6. ✅ **Frontend** — Inicia React Vite en puerto 5173 con hot reload

**Autocorrecciones integradas:**
- Si npm falla con `ERESOLVE` → reintenta con `--legacy-peer-deps`
- Si puertos 8000/5173 ya están en uso → los libera
- Si `node_modules` falta → instala dependencias
- Si backend no responde en 20s → muestra logs de error
- Si Ollama no responde → espera hasta 15s
- Si Python deps faltan → `uv sync --all-groups`

**Salida de éxito:**
```
╔════════════════════════════════════════════════════╗
║           ✅ SysMho Hunter operativo              ║
╚════════════════════════════════════════════════════╝

📍 ACCESO:
   🌐 Dashboard UI  → http://localhost:5173
   📚 API Backend   → http://localhost:8000
   📖 Swagger Docs  → http://localhost:8000/docs
   💚 Health Check  → http://localhost:8000/health
```

---

### `stop_hunter.sh` — Detiene todo correctamente

**Orden de parada (inverso al inicio):**
1. Frontend (Vite)
2. Backend (uvicorn)
3. Ollama (modelo)
4. Limpia procesos remanentes (zombies)
5. Libera puertos
6. Borra archivos `.pid`

**Garantías:**
- ✅ Primero envía SIGTERM (graceful shutdown)
- ✅ Si no responde en 5s → SIGKILL (force kill)
- ✅ Busca procesos por patrón si `.pid` file falta
- ✅ Limpia puertos residuales con `fuser -k`
- ✅ Verifica estado final de puertos

---

## 📊 Qué Significa el Output de Inicio

```
╔════════════════════════════════════════════════════╗
║  SysMho Hunter — Sistema completo de inicialización║
╚════════════════════════════════════════════════════╝

▶ Verificando prerequisitos...
✅ Todos los prerequisitos OK
```
→ Se validaron: python3, node, postgres, curl, uv instalados

```
▶ PostgreSQL...
✅ PostgreSQL activo en localhost:5432
```
→ Base de datos lista. Contiene tablas: targets, scans, findings, reports, pending_actions, logs

```
▶ Ollama (Llama 3.1 8B)...
⚠️  Modelo Llama 3.1 8B Q6_K ya en cache local
```
→ Modelo de IA local descargado y listo (~6.6 GB). Si dice "no disponible", descarga (~5-10 min)

```
▶ Backend (FastAPI)...
⚠️  Sincronizando dependencias Python (esto toma ~30s)...
✅ Dependencias Python sincronizadas
```
→ Descarga librerías Python (fastapi, sqlalchemy, anthropic, google-genai, etc)

```
⚠️  Aplicando migraciones a BD...
✅ Migraciones aplicadas exitosamente
```
→ Crea tablas en PostgreSQL según el schema de alembic

```
▶ Backend (FastAPI)...
⚠️  Esperando backend (máx 20s)...
✅ Backend activo (PID: XXXXX)
```
→ API REST escucha en http://localhost:8000. PID = ID del proceso Linux

```
▶ Frontend (React Vite)...
⚠️  node_modules no encontrado. Instalando deps npm (~60s)...
✅ Dependencias npm instaladas
```
→ Instala React, recharts, framer-motion, lucide-react, sonner, etc. Solo ocurre 1ª vez

```
✅ Frontend activo (PID: XXXXX)
```
→ Servidor Vite escucha en http://localhost:5173

```
📍 ACCESO:
   🌐 Dashboard UI  → http://localhost:5173
   📚 API Backend   → http://localhost:8000
   📖 Swagger Docs  → http://localhost:8000/docs
   💚 Health Check  → http://localhost:8000/health

📋 LOGS EN TIEMPO REAL:
   Backend   → tail -f /tmp/sysmho_backend.log
   Frontend  → tail -f /tmp/sysmho_frontend.log
   Ollama    → tail -f /tmp/sysmho_ollama.log
```

### URLs de Acceso:
- **http://localhost:5173** — Dashboard con UI (scans, findings, acciones, logs)
- **http://localhost:8000** — API REST (endpoints JSON)
- **http://localhost:8000/docs** — Swagger Interactivo (prueba endpoints sin cliente)
- **http://localhost:8000/health** — Health check (estado BD, servicios, caché)

### Monitoreo en Vivo:
```bash
# Terminal 1: Logs del backend en tiempo real
tail -f /tmp/sysmho_backend.log

# Terminal 2: Logs del frontend
tail -f /tmp/sysmho_frontend.log

# Terminal 3: Logs de Ollama (modelo local)
tail -f /tmp/sysmho_ollama.log
```

---

## 🔄 Ciclo Típico de Uso

### Sesión de Desarrollo:
```bash
# 1. Iniciar todo
bash scripts/start_hunter.sh

# 2. Abrir navegador
# http://localhost:5173

# 3. Trabajar normalmente (hot reload automático)

# 4. Ver logs en otra terminal
tail -f /tmp/sysmho_backend.log

# 5. Detener cuando termines
bash scripts/stop_hunter.sh
```

### Si Algo Falla:
```bash
# Detener todo
bash scripts/stop_hunter.sh

# Ver el problema
tail -50 /tmp/sysmho_backend.log  # ← última causa de error
tail -50 /tmp/sysmho_frontend.log

# Reintentar
bash scripts/start_hunter.sh
```

---

## 🛠️ Troubleshooting

### "Backend no responde tras 20s"
```bash
# Ver qué salió mal:
tail -30 /tmp/sysmho_backend.log

# Probable causa: migraciones fallaron
# Solución:
cd backend && uv run alembic upgrade head
bash scripts/start_hunter.sh
```

### "Puerto 8000 ya en uso"
El script auto-libera. Si persiste:
```bash
lsof -i :8000
kill -9 <PID>
```

### "Modelo Ollama tardando mucho"
```bash
# Ver progreso en otra terminal
tail -f /tmp/sysmho_ollama.log

# Primera descarga es lenta (~7GB)
# Próximas ejecuciones serán rápidas (cache local)
```

### "npm install falla con ERESOLVE"
El script ya usa `--legacy-peer-deps`. Si aún falla:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

---

## 📋 Resumen de Archivos `.pid`

El script guarda los PIDs de procesos en `$ROOT/.pids/`:
```
.pids/
├── backend.pid    # PID del proceso uvicorn
├── frontend.pid   # PID del proceso Vite
└── ollama.pid     # PID del proceso Ollama
```

Estos se usan para detención limpia y se borran automáticamente al terminar.

---

## ⚡ Tips de Eficiencia

✅ **Primera ejecución** → toma ~5-10 min (descarga modelo Llama, deps npm/Python)
✅ **Ejecuciones posteriores** → toma ~20-30s (todo en cache)
✅ **Hot reload** → cambios en código se ven automáticamente en browser
✅ **Migraciones cero-downtime** → Se aplican automáticamente sin parar BD
✅ **Puertos automáticos** → El script libera puertos ocupados
