---
name: hunter-deploy
description: Arranque controlado — verifica PostgreSQL, aplica migraciones Alembic, inicia backend y frontend en orden. Úsalo cuando necesites iniciar SysMho Hunter de forma segura.
---

Ejecuta el setup en orden secuencial:

**1. Verificar PostgreSQL:**
```bash
pg_isready -h 127.0.0.1 -p 5432 || (echo "ERROR: PostgreSQL no disponible" && exit 1)
```

**2. Aplicar migraciones:**
```bash
cd backend && uv run alembic upgrade head
```

**3. Verificar Ollama:**
```bash
curl -s http://localhost:11434/api/tags >/dev/null && echo "Ollama OK" || echo "WARN: Ollama offline — cerebro usará nivel 3 (cloud)"
```

**4. Iniciar backend (background):**
```bash
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 3 && curl -s http://localhost:8000/health
```

**5. Iniciar frontend (background):**
```bash
cd frontend && npm run dev &
```

Reporta el estado final de cada componente.
