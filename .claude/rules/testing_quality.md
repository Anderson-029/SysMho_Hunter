# Testing & Aseguramiento de Calidad

## Testing Unitarios (Python)

### Setup
- BD separada para tests (no usar DB producción)
- Fixtures en `conftest.py` para setup común
- Usar `pytest-asyncio` para tests async
- Mock solo en límites del sistema (APIs externas)

### Reglas
- Coverage mínimo: 80%
- Ejecutar: `cd backend && uv run pytest ../tests/ -v`
- Test async functions: `@pytest.mark.asyncio`
- No mockear la BD (usar BD real de test)

### Estructura
```
tests/
├── test_auth.py        # Tests de autenticación
├── test_brain.py       # Tests del cerebro híbrido
├── test_recon.py       # Tests del reconocimiento
├── test_api.py         # Tests de endpoints
└── conftest.py         # Fixtures compartidas
```

## Testing E2E (Frontend)

### Flujo Principal a Validar
```
1. Login con credenciales válidas
2. Dashboard carga correctamente
3. Mostrar username del usuario
4. Logout button visible y funciona
5. Redirect a login después de logout
```

### Tools
- Playwright o Cypress
- Tests escritos en TypeScript
- Ejecutar contra servidor dev (npm run dev)
- Screenshot en case of failure

### Ejecución
```bash
cd frontend
npx playwright test           # Ejecutar todos
npx playwright test --ui      # UI interactive
npx playwright test --headed  # Ver navegador
```

## Validación de Código

### Antes de Commit
```bash
# Backend
cd backend && uv run ruff check app/ && uv run ruff format app/
cd backend && uv run pytest ../tests/ -v

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npm run build  # Verificar que compila
```

### Linting
- **Python:** ruff (line-length=79, select E,F,W,I)
- **TypeScript:** tsc con strict mode
- **CSS:** Tailwind classes (validadas en compilación)

## Métricas de Calidad

### Backend
| Métrica | Target | Tool |
|---------|--------|------|
| Coverage | 80%+ | pytest-cov |
| PEP8 | PASS | ruff |
| Type hints | 100% | mypy (opcional) |
| Latency p95 | <500ms | timing in tests |

### Frontend
| Métrica | Target | Tool |
|---------|--------|------|
| Coverage | 70%+ | vitest/jest |
| Type check | 0 errors | tsc |
| Build | success | vite build |
| Lighthouse | 80+ | npm audit |

## Testing del Cerebro Híbrido

### Test Script (test_brain.py)
- Lanza 4 tareas representativas
- Valida que cada nivel (ML, Ollama, Cloud) responda correctamente
- Reporta % de uso por nivel
- Verifica Ollama como PRIMARY (>90% expected)

### Ejecución
```bash
cd backend && uv run python scripts/test_brain.py
```

### Resultados Esperados
- Level 1 (ML): <10ms latency
- Level 2 (Ollama): 20-40s latency
- Level 3 (Cloud): 1-3s latency
- Ollama usage: >=90% (para tareas que aplican)

## Debugging & Logs

### Ver Logs
```bash
# En tiempo real durante dev
tail -f /tmp/backend.log

# Brain decisions specifically
grep "[Brain Decision]" /tmp/backend.log

# Errores
grep "ERROR" /tmp/backend.log
```

### JSON Logging
Todos los logs importantes en JSON estructurado:
```json
{
  "timestamp": "2026-04-11T14:13:40+00:00",
  "level": "INFO",
  "event": "brain_decision",
  "brain_level": 2,
  "model": "llama3.1:8b",
  "latency_ms": 11344
}
```

## Fase 4 Plan
- [ ] Tests unitarios para auth_service.py
- [ ] Tests unitarios para brain_router.py  
- [ ] Tests E2E: login → dashboard → logout
- [ ] Coverage report en CI
- [ ] GitHub Actions pipeline
