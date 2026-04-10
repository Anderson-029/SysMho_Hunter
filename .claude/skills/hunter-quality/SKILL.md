---
name: hunter-quality
description: Auditoría completa de calidad del backend — linting ruff, formato, imports y tests. Genera un score 0-100. Úsalo antes de hacer commit.
---

Ejecuta la auditoría en 4 pasos y acumula errores:

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && uv run ruff check app/ --output-format=concise 2>&1
```

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && uv run ruff format app/ --check 2>&1
```

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter/backend && uv run python -c "from app.main import app; print('OK imports')" 2>&1
```

```bash
cd /home/anderson/Documentos/programas\ personales/SysMho_Hunter && \
uv run pytest tests/ -v --tb=short 2>&1 || echo "WARN: tests no disponibles"
```

Score: lint OK=+40, formato OK=+20, imports OK=+20, tests OK=+20.
Muestra errores concretos y comandos de corrección si score < 80.
