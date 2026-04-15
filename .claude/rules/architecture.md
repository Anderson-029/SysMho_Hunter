# Arquitectura & Decisiones Técnicas

## Patrones Críticos

### FastAPI Trailing Slash
Todos los endpoints POST/DELETE requieren trailing slash. Sin él, FastAPI devuelve 307 y curl/axios no siguen el redirect en métodos con body:
- ✅ `POST /api/v1/targets/`
- ✅ `DELETE /api/v1/targets/{id}/`
- ✅ `GET /api/v1/findings/?scan_id=...`
- ❌ `POST /api/v1/targets` → 307 redirect, falla silenciosamente

Aplica en: scripts bash (curl), frontend (axios), tests.

### Labs — Flujo de Operación
1. Usuario inicia lab manualmente (e.g., Docker: `bash auto_deploy.sh`)
2. Usuario ejecuta `bash labs/sysmho_integration.sh auto <lab> <ip> [port]`
3. Script crea target + lanza scan en SysMho Hunter API
4. Monitoreo automático hasta completion

---

## Stack Tecnológico (NO CAMBIAR)

### Backend
- **Framework:** FastAPI (async, OpenAPI docs)
- **BD:** PostgreSQL + asyncpg + SQLAlchemy 2.0+
- **Manager:** uv (no pip, no poetry)
- **Python:** 3.12+

### Frontend
- **Framework:** React 19 + Vite
- **Styling:** Tailwind CSS
- **State:** Zustand (no Redux, no Context)
- **HTTP:** Axios con interceptores
- **UI animations:** framer-motion
- **Node:** npm (no yarn)

### AI/ML
- **Nivel 1 (ML):** scikit-learn (< 10ms)
- **Nivel 2 (LLM local):** Ollama Llama 3.1 8B Q6_K (20-40s)
- **Nivel 3 (Cloud):** Gemini 2.0 Flash (1-3s)
- **Primary:** Ollama (LOCAL, no depender de cloud)

### Infraestructura
- **BD:** PostgreSQL 16+
- **LLM:** Ollama local (no API cloud para inference)
- **WebSocket:** Built-in en FastAPI
- **Logs:** JSON estructurado (ECS format future)

## Cerebro Híbrido — 3 Niveles

```
┌─────────────────────────────────────┐
│         TASK REQUEST                │
└──────────────┬──────────────────────┘
               │
        ┌──────v──────┐
        │  ML_TASKS?  │ (classify_severity, score_vuln, prioritize)
        └──────┬──────┘
               │ YES (confidence >= 0.85)
        ┌──────v──────┐
        │ Level 1: ML │────> confidence HIGH? ──YES──> RETURN
        │(scikit-learn)│
        └──────┬──────┘
               │ NO
        ┌──────v──────────────────┐
        │  LLM_TASKS or HYBRID?  │ (detect_patterns, analyze, reason)
        │ Ollama available?       │
        └──────┬──────────────────┘
               │ YES
        ┌──────v──────────────────┐
        │  Level 2: Ollama        │────> confidence >= 0.70? ──YES──> RETURN
        │  (Llama 3.1 8B)         │
        └──────┬──────────────────┘
               │ NO (OR not available)
        ┌──────v──────────────────┐
        │  Level 3: Cloud         │
        │  (Gemini 2.0 Flash)     │────> RETURN (always succeeds or error)
        └─────────────────────────┘
```

### Umbrales (Configurables en BD)
- **ML threshold:** 0.85 (alto)
- **Ollama threshold:** 0.70 (medio-alto)
- **Cloud threshold:** 0.9 (fallback, siempre acepta)

## Modelos ORM (12 Tablas)

| Tabla | Propósito | PKs |
|-------|-----------|-----|
| users | Autenticación, roles admin | UUID |
| targets | Targets para scanner | UUID |
| scopes | Scope autorizado (sin verificar) | UUID |
| scans | Instancias de scan | UUID |
| scan_tasks | Tareas dentro de scan | UUID |
| findings | Vulnerabilidades encontradas | UUID |
| evidence | Pruebas de findings | UUID |
| pending_actions | Acciones esperando aprobación | UUID |
| reports | Reportes H1 formateados | UUID |
| report_findings | Mappeo report ↔ findings | UUID |
| agent_logs | Logs de ejecución | UUID |
| brain_reasoning | Razonamientos del cerebro | UUID |
| agent_config | Configuración (umbrales, etc) | id (int) |

## Servicios Clave

### ScanService (4 fases)
1. **Recon:** subfinder, amass, httpx, nuclei (info gathering)
2. **Active:** nmap, sqlmap, ffuf (exploitation testing)
3. **Analysis:** Evidence analysis con brain (reasoning)
4. **Reporting:** Generar reporte H1 markdown

### ReportService
- Formato H1 markdown
- Templates para diferentes tipos de hallazgos
- Incluir: descripción, impact, remediation steps, proof

### AuthService
- Login con username + password
- Tokens JWT (access 30min, refresh 7 días)
- Refresh token hashing en BD
- Logout invalida refresh token

## Decisiones Arquitectónicas

### 1. JWT vs Sessions
**Decisión:** JWT (Bearer tokens)
**Razón:** SPAs modernas, stateless, mejor para APIs, CSRF-proof (tokens no auto-enviados)

### 2. Zustand vs Redux
**Decisión:** Zustand
**Razón:** Más ligero, menos boilerplate, suficiente para single-user

### 3. PostgreSQL async + asyncpg
**Decisión:** SQLAlchemy 2.0+ async
**Razón:** Non-blocking, máximo rendimiento, scales bien

### 4. Ollama LOCAL como PRIMARY
**Decisión:** Ollama en máquina local, Gemini como fallback
**Razón:** No depender de cloud, privado, control total, barato

### 5. Logging JSON estructurado
**Decisión:** JSON con timestamps ISO8601
**Razón:** Máquina-readable, fácil análisis post-incidente, integración con Elastic/Splunk

## Flujos Críticos

### Login Flow
```
POST /auth/login (username, password)
  ↓
validate credentials (hash check)
  ↓
create access_token (JWT, 30min)
  ↓
create refresh_token (JWT, 7 días)
  ↓
hash refresh_token → store en user.refresh_token_hash
  ↓
return {access_token, refresh_token, expires_in}
```

### Token Refresh
```
POST /auth/refresh (refresh_token)
  ↓
decode refresh_token
  ↓
verify type="refresh"
  ↓
hash token → compare con user.refresh_token_hash
  ↓
create NEW access_token (same refresh_token)
  ↓
return {access_token, expires_in}
```

### Scan Pipeline
```
POST /api/v1/scans (target_url, scope_id)
  ↓
validate scope (target in scope list)
  ↓
create scan record
  ↓
phase 1: recon (tools: subfinder, amass, httpx, nuclei)
  ↓
phase 2: active (tools: nmap, sqlmap, ffuf, etc)
  ↓
phase 3: analysis (brain reasoning + ML classification)
  ↓
phase 4: reporting (H1 markdown format)
  ↓
mark scan COMPLETED
```

## Consideraciones de Producción

### No Implementar Todavía
- ❌ Multi-tenancy (single-admin: Anderson)
- ❌ RBAC granular (todos public para admin)
- ❌ 2FA (nice-to-have, Fase 6)
- ❌ Webhooks (Fase 10)

### Implementar Después de Fase 4
- ✅ Blue-green deployment
- ✅ Health checks mejorados
- ✅ Graceful shutdown
- ✅ Docker Compose
- ✅ Secret rotation
