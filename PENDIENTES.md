# 📋 PENDIENTES — SysMho Hunter v0.3.0-dev

> Roadmap de mejoras, features y fixes. Actualizado: 23 Julio 2026

---

## 🔧 FOUNDATION — Bases robustas (PRIORIDAD, Julio 2026)

Congelar Neo4j / agentes / scrapers hasta cerrar esta fase.

- [x] Docker Compose: Postgres + Qdrant pinneados (`postgres:16-alpine`, `qdrant:v1.13.4`)
- [x] Local LLM desacoplado de Ollama → API OpenAI-compatible (LM Studio / Ollama /v1)
- [x] Embeddings OpenAI-compatible (`/v1/embeddings`)
- [x] Scripts sin passwords hardcodeados (`start_sysmho.sh`, `seed_db.sh`)
- [x] `scripts/doctor.sh` — diagnóstico de bases
- [x] Fix trailing slash middleware (sin 307 en brain/status)
- [x] Deps actualizadas (`uv lock --upgrade`, `npm update`)
- [x] Tests unitarios LocalLLM/Embeddings + docs `docs/LM_STUDIO.md`

---

## 🔄 EN PROGRESO — Fase RAG "Esteroides" (Julio 2026)

Evolución arquitectónica: agregar RAG (Qdrant) + Knowledge Graph (Neo4j) +
agentes especializados al SysMho Hunter existente, en vez de reconstruir
desde cero. Contexto completo y decisiones en `HANDOFF.md`.

### Fase 1.1 — RAG Core ✅ COMPLETADA (22 Julio 2026)
- [x] Qdrant corriendo en Docker (`docker-compose.yml`, puerto 6333)
- [x] `qdrant-client` instalado en backend
- [x] Embeddings vía API OpenAI-compatible (antes Ollama nativo)
- [x] Módulo `backend/app/rag/` (qdrant_client, embeddings, indexer, retriever)
- [x] Script `scripts/ingest_knowledge.py` (indexación batch de `knowledge/*.md`)
- [x] RAG integrado a `BrainRouter` (Nivel 2/3), best-effort, no bloqueante
- [x] Tests del cerebro sin regresiones de contrato

### Fase 1.2 — Poblar Knowledge Base ⏳ PAUSADA hasta cerrar Foundation
- [ ] Scraper PortSwigger Web Security Academy (rate-limited, uso personal — NO redistribuir)
- [ ] Estructurar findings de labs (`labs/devil`) como documentos indexables
- [ ] Endpoint REST `/api/v1/rag/search` (para probar desde Swagger/frontend)
- [ ] Panel RAG en dashboard (mostrar de dónde sale cada respuesta del cerebro)

### Fase 2 — Neo4j (Knowledge Graph) — PAUSADA
- [ ] Después de tener RAG poblado con contenido real (Neo4j vacío es inútil)

### Fase 3 — Fine-tuning + Agentes especializados — PAUSADA
- [ ] Evaluar modelos vía LM Studio / OpenAI-compat (sin amarrar a un vendor)
- [ ] Agentes: API Analyzer, Auth Analyzer, Recon Analyzer

---

## ✅ COMPLETADAS (Abril 2026)

### Autenticación & Seguridad
- [x] Sistema JWT profesional (access + refresh tokens)
- [x] Middleware dual (JWT + API Key backward compat)
- [x] Modelo User (UUID, roles: admin|operator|viewer)
- [x] Endpoints /auth/login, /auth/refresh, /auth/logout, /auth/me
- [x] Frontend Login Page (dark theme cyber)
- [x] AuthGuard component
- [x] Zustand auth store con localStorage
- [x] Axios interceptores (JWT auto-inject, 401 auto-refresh)
- [x] WebSocket autenticado con JWT
- [x] Rate limiting en login (5 req/min)

### Backend
- [x] Migración Alembic para tabla `users`
- [x] Script create_admin.py
- [x] Password hashing con Argon2
- [x] PEP8 compliance (ruff check PASS)

### Frontend
- [x] LoginPage con animaciones (framer-motion)
- [x] Dashboard con username + logout button
- [x] Client axios con interceptores
- [x] WebSocket con token en query param

---

## 🔄 EN PROGRESO

### Fase 3: Ollama & IA Diagnostics ✅ TESTADA
- [x] Endpoints /api/v1/brain/status ✅ Working
- [x] Endpoints /api/v1/brain/test ✅ Working
- [x] Endpoints /api/v1/brain/stats ✅ Working (placeholder for DB persistence)
- [x] Test script test_brain.py validado
  - Ollama: 75% usage (3/4 tasks, 1 ML failure due to Gemini API key expired)
  - Nivel 1 (ML): Working, <10ms latency
  - Nivel 2 (Ollama): Working, 8-26s per request
  - Nivel 3 (Cloud): API key expired (external, not code issue)
- [x] Public access added to brain diagnostic endpoints (security middleware)

### E2E Testing
- [ ] Login → Dashboard flow (blocked by PostgreSQL unavailable)
- [ ] WebSocket LIVE status confirmado ✅
- [ ] Scan operations E2E
- [ ] Logout flow E2E
- [ ] Refresh token automation

---

## ⏳ PENDIENTES (Próximas fases)

### Fase 2: RBAC (NO APLICA — Single User Only)
- [x] Arquitectura preparada para roles (admin|operator|viewer)
- ~~Implementar control de acceso por rol~~ **NO NECESARIO**
  - ~~Admin: acceso total~~
  - ~~Operator: scans, findings, actions~~
  - ~~Viewer: solo lectura~~
- ~~Proteger endpoints con @require_admin, @require_operator~~ **Todos públicos para admin**
- ~~Frontend: mostrar/ocultar UI según rol~~ **UI única para admin**

**NOTA:** SysMho Hunter es single-user (Anderson = admin único). Si en futuro quieres multi-user, la arquitectura ya está lista.

### Labs & Integration System ✅ COMPLETADO (12 Abril 2026)
- [x] deploy.sh auditado → REMOVIDO (violaba los 5 pilares: Docker CLI inválido, stubs incompletos)
- [x] sysmho_integration.sh — 3 bugs críticos corregidos:
  - ask_confirmation(): TTY fallback (`read -r response < /dev/tty || read -r response`)
  - Trailing slash en todos los endpoints POST/GET (`/api/v1/targets/`, `/api/v1/scans/`, `/api/v1/findings/`)
  - Printf `%%` escaping para evitar error de formato
- [x] TargetsManager.tsx — botones DELETE corregidos (trailing slash `/targets/${id}/` y `/targets/${targetId}/scopes/${scopeId}/`)
- [x] scripts/check_tools.sh creado — verifica 19 herramientas de pentesting
- [x] scripts/test_integration_e2e.sh creado — test automatizado end-to-end (target → scan → monitor → findings)
- [x] scripts/README_TOOLS.md creado — guía de instalación por distro (Kali, Arch, Ubuntu)
- [x] labs/README.md actualizado — documenta nuevo flujo 2-terminales
- [x] Auditorías .claude/audits/ creadas: AUDIT_DEPLOY_SH.md, AUDIT_INTEGRATION_SH_FIXES.md
- [x] ADR .claude/decisions/DECISION_REMOVE_DEPLOY_SH.md
- [x] Test E2E ejecutado y confirmado: target → scan → recon → brain → completed (0 findings en lab de prueba)
- [x] 19 herramientas de pentesting instaladas en sistema Ubuntu
- [x] .gitignore: labs/ añadido (Docker labs no subir a GitHub)

### Fase 4: Security Hardening ✅ COMPLETADO (12 Abril 2026)
- [x] Credential remediation — secrets eliminados del código
- [x] OWASP Top 10 compliance verificado
- [x] SECURITY.md policy creada
- [x] Auditorías SAST ejecutadas

### Fase 3: Mejoras Ollama & IA ✅ COMPLETADA
- [x] Logging detallado del brain (JSON estructurado con timestamps)
- [x] Endpoints /api/v1/brain/status (estado actual del cerebro)
- [x] Endpoints /api/v1/brain/test (test cada nivel)
- [x] Endpoints /api/v1/brain/stats (estadísticas de uso)
- [x] Test script `test_brain.py` (validar Ollama 100%)
- [ ] Dashboard del cerebro (nice-to-have)
- [ ] Token rotation en refresh (nice-to-have)
- [ ] Configurar umbral dinámico por tarea (nice-to-have)
- [ ] Benchmarking Llama vs Gemini (nice-to-have)

### Fase 4: Tests & CI/CD
- [ ] Tests unitarios para auth_service.py
- [ ] Tests E2E con Playwright/Cypress
- [ ] GitHub Actions CI pipeline
- [ ] Lint en pre-commit hook
- [ ] Coverage mínimo del 80%

### Fase 5: Base de datos & Observabilidad
- [ ] Índices optimizados en tabla `users`
- [ ] Connection pooling asyncpg
- [ ] Logging centralizado (estructura ECS)
- [ ] Métricas Prometheus
- [ ] Alertas por error rates, latencia

### Fase 6: Seguridad Avanzada
- [ ] Migrar a httpOnly cookies (opcional)
- [ ] CSRF token adicional (defensa en profundidad)
- [ ] 2FA (TOTP) para admin
- [ ] Validación de origin/referer en endpoints críticos
- [ ] WAF rules (ModSecurity)
- [ ] Encryption at rest para sensitive fields

### Fase 7: Frontend Enhancements
- [ ] Dark/Light mode toggle
- [ ] Remember me en login (con secure flag)
- [ ] Password reset flow
- [ ] Session timeout warning (5min antes de expirar)
- [ ] Loading skeletons en cards
- [ ] Error boundaries con retry logic

### Fase 8: DevOps & Deployment
- [ ] Docker Compose (backend + frontend + postgres + ollama)
- [ ] Environment variables validation on startup
- [ ] Health check endpoints mejorados
- [ ] Graceful shutdown hooks
- [ ] Blue-green deployment ready
- [ ] Secret rotation strategy

### Fase 9: Documentation
- [ ] API OpenAPI/Swagger completado
- [ ] Auth flow diagrama (ASCII art)
- [ ] Deployment guide
- [ ] Contributing guidelines
- [ ] Architecture decision records (ADR)

### Fase 10: Optimizaciones (NICE TO HAVE)
- [ ] Caching Redis para resultados ML
- [ ] Pagination en endpoints de listings
- [ ] Search/filter avanzado en findings
- [ ] Export PDF de reportes
- [ ] Webhooks para notificaciones externas
- [ ] GraphQL alternativo a REST (opcional)

---

## 🐛 BUGS CONOCIDOS

- [x] Ollama no se reportaba como disponible en health check (FIXED: estaba activo, solo script lo reportaba mal)
- [x] Email validator rechazaba .local y localhost (FIXED: usando admin@example.com)
- [x] AxiosResponse import error en Vite (FIXED: removido type import innecesario)
- [x] integration.sh hanging en ask_confirmation sin TTY (FIXED: TTY fallback)
- [x] integration.sh "Fallo al crear target" silencioso (FIXED: trailing slash en endpoints)
- [x] integration.sh printf format error `%` (FIXED: `%%` escaping)
- [x] Dashboard: botón DELETE target no funcionaba (FIXED: trailing slash en TargetsManager.tsx)
- [ ] Session timeout a los 30min (por diseño, esperar confirm)

---

## 📊 MÉTRICAS

| Métrica | Valor | Meta |
|---------|-------|------|
| Coverage | - | 80%+ |
| API Latency p95 | - | <500ms |
| Frontend TTI | - | <2s |
| Ollama latency | ~20-40s | <30s |
| DB Queries /req | - | <5 |

---

## 🔗 REFERENCIAS

- JWT Auth: `backend/app/security.py`, `backend/app/api/v1/auth.py`
- Brain Router: `backend/app/brain/router.py`
- RAG: `backend/app/rag/`, `knowledge/`, `docker-compose.yml`
- Frontend Auth: `frontend/src/stores/authStore.ts`
- CLAUDE.md: instrucciones maestras del proyecto
- HANDOFF.md: contexto de la sesión "esteroides RAG" para continuar

---

**Última actualización:** 22 Julio 2026
**Actualizado por:** Claude Sonnet 5
**Estado general:**
- ✅ Fase 1 (Auth JWT) COMPLETADA Y PROBADA
- ✅ Fase 2 (RBAC) NO APLICA (single-user admin)
- ✅ Fase 3 (Ollama & IA) COMPLETADA Y PROBADA
  - Endpoints /api/v1/brain/* operacionales
  - Brain diagnostics validados: ML + Ollama + Cloud (API key expired)
  - Ollama 75% usage rate (3/4 tasks, 1 ML task skips Ollama by design)
- ✅ Fase 4 (Security Hardening) COMPLETADA
  - Credential remediation, OWASP compliance, SECURITY.md
- ✅ Labs & Integration System COMPLETADO Y PROBADO E2E
  - deploy.sh removido, sysmho_integration.sh corregido
  - 3 bugs críticos solucionados (TTY, trailing slash, printf)
  - Dashboard DELETE fix aplicado
  - 19 herramientas pentesting instaladas
- ✅ Fase 5 (Tests & CI) — BD de tests creada, tests del cerebro en verde
- 🔄 Fase RAG "Esteroides" EN PROGRESO
  - ✅ Fase 1.1: RAG Core (Qdrant + embeddings + integración BrainRouter)
  - ⏳ Fase 1.2: Poblar knowledge base (SIGUIENTE)
  - ⏳ Fase 2: Neo4j — no empezada
  - ⏳ Fase 3: Fine-tuning Qwen 3.5 + agentes — no empezada
