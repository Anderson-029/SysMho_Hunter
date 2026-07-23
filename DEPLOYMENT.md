# 🚀 DEPLOYMENT.md — Guía de Despliegue en Otro Dispositivo

> Guía completa para levantar SysMho Hunter en una máquina nueva (Linux, macOS
> o Windows), partiendo de un `git clone` limpio. Cubre exactamente qué llega
> por git, qué NO llega (y por qué), y qué debe generar/instalar el usuario a
> mano en cada paso.

---

## 0. Qué SÍ y qué NO viaja en el repositorio

Cuando clones el repo, **no vas a tener una copia 1:1 del entorno de trabajo**.
Hay archivos y carpetas excluidos deliberadamente por `.gitignore`. Si no
sabes esto de antemano, el sistema simplemente no arrancará y no vas a
entender por qué.

### ❌ NO viene en git (tenés que crearlo/generarlo vos)

| Path | Por qué está excluido | Qué hacer |
|------|------------------------|-----------|
| `backend/.env` | Contiene secrets (passwords, API keys, JWT secret). **Es el único `.env` que el backend realmente lee** (`config.py` usa `env_file=".env"` relativo, y todo se ejecuta con `cd backend`) | Copiar de `backend/.env.example` y rellenar valores reales (paso 5) |
| `.env.test` (en la **raíz** del proyecto, no en `backend/`) | Config de BD de tests, también secrets. `tests/conftest.py` busca este archivo específicamente en la raíz (`_PROJECT_ROOT / ".env.test"`) | Crear manualmente si vas a correr tests (paso 10) |
| `backend/.venv/` | Entorno virtual Python, se regenera con `uv sync` | `uv sync` lo recrea (paso 4) |
| `frontend/node_modules/` | Dependencias npm, se regeneran con `npm install` | `npm install` (paso 6) |
| `ml/models/*.pkl` `*.joblib` | Modelos ML entrenados (pesan varios MB, no son código) | Ver sección 4 — **debes copiarlos manualmente o reentrenar** |
| `ml/data/raw/`, `ml/data/processed/` | Datasets de entrenamiento | Igual que arriba |
| `labs/` | Labs Docker (`.tar` de máquinas vulnerables, pesan cientos de MB) | Opcional — solo si vas a hacer pruebas con labs (paso 10) |
| `logs/`, `.pids/` | Runtime, se generan solos al arrancar | No hacer nada |
| `.pytest_cache/`, `__pycache__/` | Caché de Python | No hacer nada |
| `frontend/dist/` | Build de producción del frontend | Se genera con `npm run build` si lo necesitás |
| Modelo Ollama / LM Studio | Pesan GBs, viven fuera del repo | Ver `docs/LM_STUDIO.md` |
| Datos de PostgreSQL | Volumen Docker `postgres_data` | `docker compose up -d` + Alembic |
| Datos de Qdrant (`qdrant_data` volumen Docker) | Vector DB, se genera al indexar `knowledge/` | Reindexar con `ingest_knowledge.py` (paso 8) |

> ⚠️ **`.env` en la raíz:** Docker Compose lee `.env` en la raíz para
> sustituir `DB_*`. El backend **solo** lee `backend/.env`. Mantén ambos
> alineados en passwords de BD.

### ✅ SÍ viene en git (no hay que hacer nada especial)

- Todo el código fuente: `backend/app/`, `frontend/src/`
- `backend/pyproject.toml` + `backend/uv.lock` (deps exactas y reproducibles)
- `frontend/package.json` (deps, sin lockfile propio verificado — revisar si existe `package-lock.json`)
- `backend/migrations/` (Alembic — recrea el schema completo de BD)
- `docker-compose.yml` (definición de Qdrant)
- `knowledge/*.md` (contenido a indexar en RAG)
- Todos los `.md` de documentación (`CLAUDE.md`, `AGENTS.md`, etc.)
- `.env.example` (plantilla, sin secrets reales)
- `scripts/*.sh` y `scripts/*.py`

---

## 1. Requisitos Previos por Sistema Operativo

SysMho Hunter usa herramientas CLI de pentesting (nmap, sqlmap, nuclei, etc.)
que son **nativas de Linux**. Esto determina la estrategia según tu SO.

### 🐧 Linux (Ubuntu/Debian/Kali/Parrot/Arch) — Soporte nativo completo

Es el entorno recomendado y el único donde el arsenal de 19 herramientas
funciona sin capas de compatibilidad.

| Componente | Versión mínima | Instalación |
|---|---|---|
| Python | 3.12+ | `sudo apt install python3.12` (o gestor de tu distro) |
| Node.js | 20+ | `sudo apt install nodejs npm` o [nvm](https://github.com/nvm-sh/nvm) |
| PostgreSQL | 16+ | `sudo apt install postgresql` |
| Docker + Docker Compose | reciente | `sudo apt install docker.io docker-compose-plugin` |
| uv (gestor Python) | última | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Ollama | última | `curl -fsSL https://ollama.com/install.sh \| sh` |
| git | cualquiera | `sudo apt install git` |

### 🍎 macOS — Soporte casi completo (algunas tools vía Homebrew)

> El usuario escribió "iOS" pero SysMho Hunter **no corre en iOS** (no es un
> sistema para servidores/backends — no hay Docker, no hay proceso en segundo
> plano persistente tipo uvicorn). Esta sección asume **macOS** (Mac de
> escritorio/laptop), que sí es viable.

| Componente | Instalación |
|---|---|
| Homebrew | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Python 3.12+ | `brew install python@3.12` |
| Node.js 20+ | `brew install node` |
| PostgreSQL 16+ | `brew install postgresql@16 && brew services start postgresql@16` |
| Docker Desktop | Descargar de docker.com (necesario para Qdrant) |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Ollama | `brew install ollama` o app nativa de ollama.com |
| Herramientas CLI de pentesting | `brew install nmap sqlmap nikto whatweb wfuzz` — el resto (`ffuf`, `nuclei`, `subfinder`, `amass`, `gobuster`, `httpx`, etc.) vía `go install`, ver `scripts/README_TOOLS.md` |

**Limitación conocida:** `masscan` y algunas tools Go/Rust pueden requerir
compilación manual en macOS (arquitectura ARM en Apple Silicon vs x86). Si
una herramienta falla, `SysMho Hunter no crashea` — solo marca esa
`scan_task` como `skipped` (ver `backend/app/recon/AGENTS.md`).

### 🪟 Windows — Requiere WSL2 (no correr nativo en PowerShell/CMD)

**No se recomienda instalar directamente en Windows nativo.** El backend usa
`asyncio.create_subprocess_exec` para invocar binarios de Linux (nmap,
sqlmap, etc. en su forma CLI de Linux) y varios scripts son Bash (`.sh`).
La única forma soportada y coherente con el resto del proyecto es:

1. **Instalar WSL2** (Windows Subsystem for Linux):
   ```powershell
   # PowerShell como Administrador
   wsl --install -d Ubuntu-24.04
   ```
   Reiniciar cuando lo pida. Esto instala un Ubuntu real dentro de Windows.

2. **Abrir la terminal de Ubuntu (WSL)** y seguir **exactamente los mismos
   pasos que la sección Linux** de esta guía, dentro de esa terminal.

3. **Docker:** instalar **Docker Desktop para Windows** con integración WSL2
   habilitada (Settings → Resources → WSL Integration → activar tu
   distro Ubuntu). Así `docker compose` funciona desde dentro de WSL.

4. **Acceso desde el navegador de Windows:** WSL2 expone `localhost`
   automáticamente al host Windows, así que `http://localhost:5173` y
   `http://localhost:8000` funcionan igual desde el navegador de Windows
   sin configuración extra.

5. **Ollama:** podés instalar Ollama nativo de Windows (tiene instalador
   `.exe`) o dentro de WSL — cualquiera de los dos expone
   `http://localhost:11434` igual. Se recomienda el nativo de Windows si
   tenés GPU NVIDIA, por mejor soporte de drivers CUDA.

6. **PostgreSQL:** correrlo dentro de WSL (`sudo apt install postgresql`)
   es más simple que lidiar con el instalador nativo de Windows + auth.

> **Resumen Windows:** todo el trabajo real ocurre "como si fuera Linux"
> dentro de WSL2. Windows solo aporta el navegador y Docker Desktop como
> capa gráfica.

---

## 2. Clonar el repositorio

```bash
git clone <URL_DEL_REPO> SysMho_Hunter
cd SysMho_Hunter
```

Verificar que llegaron los archivos esperados (ver sección 0 para lo que
falta a propósito):

```bash
ls -la
# Deberías ver: backend/ frontend/ knowledge/ scripts/ CLAUDE.md
# .env.example docker-compose.yml pyproject.toml (dentro de backend/)
# NO vas a ver: backend/.env, backend/.venv/, frontend/node_modules/,
# ml/models/*.pkl, labs/*.tar
```

---

## 3. Instalar y arrancar servicios base

### 3.1 PostgreSQL + Qdrant (Docker Compose)

```bash
# Copiar plantilla de compose (raíz) y backend
cp .env.example .env          # DB_* para compose
cp backend/.env.example backend/.env
# Editar passwords y LOCAL_LLM_* (ver docs/LM_STUDIO.md)

# Si hay un Postgres del sistema en :5432, detenlo primero.
docker compose up -d

# Verificar
docker compose ps
curl http://localhost:6333/readyz
```

### 3.2 Local LLM (OpenAI-compatible)

No se requiere Ollama. Usa LM Studio (u otro servidor `/v1`):

Ver guía completa: [`docs/LM_STUDIO.md`](docs/LM_STUDIO.md)

```bash
# Ejemplo LM Studio
# LOCAL_LLM_BASE_URL=http://localhost:1234/v1
# LOCAL_LLM_MODEL=<id del modelo cargado>
curl -s http://localhost:1234/v1/models -H "Authorization: Bearer lm-studio"
```

### 3.3 Docker + Qdrant (incluido en 3.1)

```bash
docker compose up -d
curl http://localhost:6333/readyz
```

**En Linux, si nunca usaste Docker sin sudo:**
```bash
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar (o reiniciar) para que el grupo aplique
```

---

## 4. Modelos ML (`ml/models/*.pkl`) — el paso que más se olvida

Estos archivos **no están en git** (`.gitignore` los excluye por peso: son
binarios de varios MB cada uno, no tiene sentido versionarlos como código).
El `BrainRouter` Nivel 1 (scikit-learn) los necesita para `classify_severity`,
`score_vuln`, `prioritize_targets` y como *fallback* de `detect_patterns`.

Tenés dos opciones:

### Opción A — Copiar los `.pkl` desde la máquina original (recomendado)
```bash
# Desde la máquina vieja, comprimir y transferir (scp, USB, etc.)
tar -czf ml_models.tar.gz ml/models/*.pkl ml/models/model_metadata.json

# En la máquina nueva, dentro de SysMho_Hunter/
tar -xzf ml_models.tar.gz
```

### Opción B — Reentrenar desde cero
```bash
cd ml/training
# Revisar ml/scripts/ y ml/notebooks/ para el pipeline de entrenamiento
# (requiere datasets en ml/data/raw/, que TAMPOCO vienen en git)
```

**Si no tenés los `.pkl` ni los reentrenás:** el sistema **no crashea** —
`MLEngine` maneja la ausencia de modelos con gracia y el `BrainRouter` escala
directo a Nivel 2 (Ollama) para todo. Es funcionalmente correcto pero pierde
la ventaja de latencia <10ms del Nivel 1. Confirmalo con:

```bash
curl http://localhost:8000/api/v1/brain/status
```

---

## 5. Backend — Python + `.env`

### 5.1 Instalar `uv` y dependencias

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # si no lo instalaste antes

cd backend
uv sync   # lee pyproject.toml + uv.lock, crea backend/.venv/ automáticamente
```

### 5.2 Crear el `.env` real

```bash
cp .env.example .env
```

Editar `backend/.env` y completar **todos** estos valores (ninguno tiene
default seguro, todos son obligatorios para arrancar):

| Variable | Cómo obtenerla |
|---|---|
| `DB_PASSWORD` | La que usaste al crear el usuario postgres en el paso 3.1 |
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey (gratis, con límite de requests/min) |
| `API_KEY` | Generar: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SECRET_KEY` | Generar igual que arriba (otra clave distinta, para JWT) |
| `ADMIN_PASSWORD` | Elegir una password fuerte para el usuario admin |
| `QDRANT_URL` | Dejar `http://localhost:6333` si Docker corre local |

⚠️ **Nunca compartas ni commitees este archivo.** Si en algún momento pegás
su contenido en un chat (con Claude, con quien sea), rotá esas claves
después — quedan expuestas igual aunque el archivo no se suba a git.

---

## 6. Frontend — Node + npm

```bash
cd frontend
npm install
# Si da error ERESOLVE (conflictos de peer deps):
npm install --legacy-peer-deps
```

No hace falta `.env` en frontend salvo que cambies la URL del backend
(por defecto asume `http://localhost:8000`). Si necesitás configurarlo,
crear `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
```

---

## 7. Migraciones de Base de Datos

```bash
cd backend
uv run alembic upgrade head
```

Esto crea las 12 tablas (`targets`, `scopes`, `scans`, `scan_tasks`,
`findings`, `evidence`, `pending_actions`, `reports`, `report_findings`,
`agent_logs`, `brain_reasoning`, `agent_config`, `users`) desde cero, ya
que la BD nueva empieza vacía (no viene con datos).

### 7.1 Sembrar configuración inicial

```bash
cd ..   # volver a la raíz del proyecto
bash scripts/seed_db.sh
```

Esto inserta los umbrales por defecto en `agent_config` (ver
`backend/AGENTS.md` para la tabla completa de keys).

### 7.2 Crear usuario admin

```bash
cd backend
uv run python scripts/create_admin.py
# Lee ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD de .env
```

---

## 8. RAG — Indexar la Knowledge Base

Qdrant arranca vacío (los vectores no viven en git, solo el contenido fuente
en `knowledge/*.md`). Hay que indexarlo manualmente una vez:

```bash
cd backend
uv run python ../scripts/ingest_knowledge.py
```

Verificar:
```bash
curl http://localhost:6333/collections/security_knowledge | python3 -m json.tool
```

Si agregás nuevos documentos a `knowledge/` más adelante, volvé a correr
este script (es idempotente, actualiza por `id` del chunk).

---

## 9. Herramientas de Pentesting (arsenal de 19 tools)

```bash
bash scripts/check_tools.sh              # ver qué falta
bash scripts/check_tools.sh --install     # instalar automáticamente lo que falte
# o directamente:
bash scripts/install_tools.sh
```

Ver `scripts/README_TOOLS.md` para instalación manual por distro si el
script automático falla en algo puntual. **El sistema no crashea si faltan
herramientas** — cada `scan_task` de una tool ausente se marca `skipped` y
el pipeline continúa, pero el scan será menos completo.

---

## 10. Tests (opcional, recomendado antes de tocar código)

```bash
# Crear BD separada de tests
sudo -u postgres createdb sysmho_hunter_test

# Crear .env.test EN LA RAÍZ del proyecto (NO en backend/) — así lo busca
# tests/conftest.py. No viene en git, es config con secrets.
cat > .env.test << 'EOF'
TEST_DATABASE_URL=postgresql+asyncpg://postgres:tu_password_aqui@127.0.0.1/sysmho_hunter_test
TEST_API_URL=http://localhost:8000
DEBUG=false
ENVIRONMENT=test
EOF

cd backend
uv run pytest ../tests/ -v
```

---

## 11. Labs de práctica (opcional)

Los archivos `.tar` de las máquinas Docker vulnerables **no vienen en git**
(pesan cientos de MB, y están gitignored explícitamente). Si querés
practicar con `labs/devil`:

1. Conseguir el `.tar` de la máquina desde donde la tengas guardada (no se
   distribuye por git — transferir manualmente, USB, almacenamiento propio)
2. Colocarlo en `labs/devil/devil.tar`
3. Seguir `labs/README.md` (flujo de 2 terminales: `auto_deploy.sh` +
   `sysmho_integration.sh`)

Si no te importan los labs, saltate este paso completo — no afecta el
funcionamiento del sistema principal.

---

## 12. Arrancar todo

```bash
bash scripts/start_hunter.sh
```

Este script (ver `SCRIPTS_GUIDE.md` para el detalle completo) valida
prerequisitos, arranca PostgreSQL/Ollama si hace falta, aplica migraciones
pendientes, levanta backend (puerto 8000) y frontend (puerto 5173).

Accesos:
- Dashboard: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Para detener todo:
```bash
bash scripts/stop_hunter.sh
```

---

## 13. Checklist Final — Verificación Completa

Marcá cada uno antes de dar por "andando" el sistema en la máquina nueva:

- [ ] `python3 --version` → 3.12+
- [ ] `node --version` → 20+
- [ ] `uv --version` instalado
- [ ] `docker ps` funciona sin `sudo` (o con `sudo` si preferís)
- [ ] PostgreSQL corriendo, BD `sysmho_hunter` creada
- [ ] `backend/.env` existe y **todas** sus variables están rellenas (no placeholders)
- [ ] `ollama list` muestra `llama3.1:8b-instruct-q6_K` y `nomic-embed-text`
- [ ] `docker compose up -d qdrant` corriendo, `curl localhost:6333/healthz` responde
- [ ] `ml/models/*.pkl` presentes (copiados o reentrenados) — o aceptado que Nivel 1 ML no estará disponible
- [ ] `cd backend && uv sync` sin errores
- [ ] `cd frontend && npm install` sin errores
- [ ] `uv run alembic upgrade head` aplicado sin errores
- [ ] `bash scripts/seed_db.sh` ejecutado
- [ ] Usuario admin creado (`create_admin.py`)
- [ ] `ingest_knowledge.py` corrido al menos una vez (RAG poblado)
- [ ] `bash scripts/check_tools.sh` — arsenal de pentesting instalado (o aceptado que faltan algunas)
- [ ] `bash scripts/start_hunter.sh` levanta sin errores
- [ ] Login exitoso en http://localhost:5173 con el usuario admin creado
- [ ] `curl http://localhost:8000/health` responde `{"status": "online", ...}`

---

## 14. Problemas Comunes al Migrar de Máquina

| Síntoma | Causa | Solución |
|---|---|---|
| Backend no arranca, error de import `app` | `uv sync` no corrió, o corriste `uvicorn` fuera de `backend/` | `cd backend && uv sync` y ejecutar comandos desde ahí |
| `relation "targets" does not exist` | Migraciones no aplicadas en la BD nueva | `uv run alembic upgrade head` |
| Brain siempre usa Nivel 2 (Ollama), nunca Nivel 1 | Faltan `ml/models/*.pkl` (no vienen en git) | Ver sección 4 |
| RAG no devuelve contexto (`[Retriever]` vacío) | Qdrant vacío, nunca se indexó | `uv run python ../scripts/ingest_knowledge.py` |
| `docker: permission denied` | Usuario no está en grupo `docker` | `sudo usermod -aG docker $USER` + reiniciar sesión |
| Scans fallan en casi todas las tools | Arsenal de pentesting no instalado en la máquina nueva | `bash scripts/check_tools.sh --install` |
| `GEMINI_API_KEY` inválida / cuota agotada | Key de la máquina vieja no se copió, o expiró | Generar una nueva en aistudio.google.com, actualizar `.env` |
| Login falla con "usuario no encontrado" | Nunca se corrió `create_admin.py` en la BD nueva | `cd backend && uv run python scripts/create_admin.py` |
| Windows: nada de esto funciona en PowerShell directo | Se intentó instalar nativo en Windows en vez de WSL2 | Usar WSL2 desde el inicio (sección 1) |
| macOS: `masscan` o alguna tool Go no compila | Limitación de arquitectura ARM (Apple Silicon) | Revisar alternativa en `scripts/README_TOOLS.md`, o aceptar esa tool como `skipped` |

---

## 15. Resumen Ultra-Rápido (para quien ya leyó todo una vez)

```bash
git clone <repo> && cd SysMho_Hunter

# Servicios base
sudo systemctl start postgresql
ollama serve &
ollama pull llama3.1:8b-instruct-q6_K
ollama pull nomic-embed-text
docker compose up -d qdrant

# ml/models/*.pkl → copiar manualmente desde máquina origen (no viene en git)

# Backend
cd backend
cp .env.example .env   # ← EDITAR y rellenar TODOS los valores
uv sync
uv run alembic upgrade head
cd .. && bash scripts/seed_db.sh
cd backend && uv run python scripts/create_admin.py
uv run python ../scripts/ingest_knowledge.py

# Frontend
cd ../frontend && npm install

# Arsenal de pentesting
cd .. && bash scripts/check_tools.sh --install

# Arrancar
bash scripts/start_hunter.sh
```

---

**Última actualización:** 23 Julio 2026
**Mantenido por:** Anderson (SysMho Hunter, single-admin)
