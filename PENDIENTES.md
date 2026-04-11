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

### E2E Testing
- [ ] Login → Dashboard flow validado ✅ (manual)
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

### Fase 3: Mejoras Ollama & IA
- [ ] Verificar que Ollama es usado 100% antes de Gemini
- [ ] Logging detallado del brain (qué nivel se usó, por qué)
- [ ] Implementar token rotation en refresh (seguridad)
- [ ] Dashboard del cerebro: mostrar latencia por nivel
- [ ] Configurar umbral de confianza dinámico por tarea
- [ ] Benchmarking Llama vs Gemini (cost, quality, speed)

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
**Estado general:** ✅ Fase 1 (Auth) COMPLETADA — Fase 2 (RBAC) NO APLICA — Listo para Fase 3 (IA & Optimizaciones)
