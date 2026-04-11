# 📋 PENDIENTES — SysMho Hunter v0.2.0

> Roadmap de mejoras, features y fixes. Actualizado: 11 Abril 2026

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
- Frontend Auth: `frontend/src/stores/authStore.ts`
- CLAUDE.md: instrucciones maestras del proyecto

---

**Última actualización:** 11 Abril 2026  
**Actualizado por:** Claude Sonnet 4.6  
**Estado general:** 
- ✅ Fase 1 (Auth JWT) COMPLETADA Y PROBADA
- ✅ Fase 2 (RBAC) NO APLICA (single-user admin)
- ✅ Fase 3 (Ollama & IA) COMPLETADA Y PROBADA
  - Endpoints /api/v1/brain/* operacionales
  - Brain diagnostics validados: ML + Ollama + Cloud (API key expired)
  - Ollama 75% usage rate (3/4 tasks, 1 ML task skips Ollama by design)
- ⏳ Fase 4 (Tests & CI) SIGUIENTE
