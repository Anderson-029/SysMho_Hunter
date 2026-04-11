# 📋 .claude/rules — Reglas del Proyecto SysMho Hunter

Esta carpeta contiene las reglas y guías técnicas del proyecto. Están organizadas por tema para fácil referencia.

## 📁 Estructura

| Archivo | Tema | Usar cuando... |
|---------|------|------------------|
| `backend_python.md` | Python, uv, async, BD, PEP8 | Escribas código backend o modifiques estructura Python |
| `frontend_react.md` | React, TypeScript, Zustand, CSS | Desarrolles frontend o UI components |
| `security_pentesting.md` | Seguridad, auth, pentesting, scope | Toques autenticación, payloads o operaciones sensibles |
| `testing_quality.md` | Tests, coverage, validación, debugging | Escribas tests o valides calidad de código |
| `architecture.md` | Stack, decisiones técnicas, flujos | Necesites entender decisiones de diseño o cómo funcionan los flujos |

## 🎯 5 Pilares Obligatorios

Cada línea de código debe cumplir:
1. **Coherencia** — Código consistente
2. **Congruencia** — Todo alineado
3. **Funcionalidad** — Features funcionan exactamente
4. **Estabilidad** — Cero crashes
5. **Seguridad Total** — Cero vulnerabilidades

## ⚡ Quick Start

### Backend
```bash
cd backend
uv sync                           # Instalar deps
uv run ruff check app/           # Validar PEP8
uv run pytest ../tests/ -v       # Tests
uv run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npx tsc --noEmit                 # Verificar tipos
npm run dev
```

### Validación Pre-Commit
```bash
# Backend
cd backend && uv run ruff check app/ && uv run ruff format app/ && uv run pytest ../tests/ -v

# Frontend
cd frontend && npx tsc --noEmit && npm run build
```

## 🚀 Procesos Principales

| Proceso | Puerto | Comando |
|---------|--------|---------|
| Backend API | 8000 | `cd backend && uv run uvicorn app.main:app --reload` |
| Frontend UI | 5173 | `cd frontend && npm run dev` |
| PostgreSQL | 5432 | `systemctl start postgresql` |
| Ollama (LLM) | 11434 | `ollama serve` |

## 📖 Referencia Rápida

### Crear Nuevo Endpoint
1. Crear modelo en `app/models/`
2. Crear schema en `app/schemas/`
3. Crear servicio en `app/services/`
4. Crear endpoint en `app/api/v1/`
5. Verificar: PEP8, tipos, auth, tests

### Agregar Nueva Dependencia
```bash
cd backend
uv add package-name
uv sync
```

### Crear Migración BD
```bash
cd backend
uv run alembic revision --autogenerate -m "descripcion"
uv run alembic upgrade head
```

### Escribir Test
```bash
# tests/test_feature.py
@pytest.mark.asyncio
async def test_something():
    ...
```

## 🔒 Seguridad Primero

- ✅ Validar scope antes de ejecutar herramientas
- ✅ Secrets en .env (NUNCA en código)
- ✅ JWT con dual-mode (Bearer + API Key)
- ✅ Payloads no destructivos por defecto
- ✅ Logging de acciones críticas
- ✅ Aprobar operaciones high-risk explícitamente

## 📊 Métricas de Éxito

- ✅ Coverage: 80% (backend), 70% (frontend)
- ✅ Latency p95: <500ms
- ✅ PEP8: PASS (ruff)
- ✅ TypeScript: 0 errors
- ✅ Ollama usage: 90%+ para tareas aplicables

## 🤔 ¿Preguntas?

- Revisa `CLAUDE.md` en raíz del proyecto para instrucciones maestras
- Revisa `PENDIENTES.md` para estado de fases
- Revisa memoria en `.claude/projects/.../memory/` para contexto de decisiones pasadas

---

**Última actualización:** 11 Abril 2026  
**Autoridad:** Anderson (único admin, SysMho Hunter)
