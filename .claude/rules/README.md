# 📋 .claude/rules — Reglas del Proyecto SysMho Hunter (CLI)

Reglas y guías técnicas del proyecto, organizadas por tema.

## 📁 Estructura

| Archivo | Tema | Usar cuando... |
|---------|------|------------------|
| `backend_python.md` | Python, uv, async, PEP8, estructura CLI | Escribas o modifiques código Python |
| `security_pentesting.md` | Scope, payloads, aprobación, auditoría | Toques scope, payloads u operaciones sensibles |
| `testing_quality.md` | Tests, ruff, validación, 6 pilares | Escribas tests o valides calidad |
| `recon_methodology.md` | Metodología de reconocimiento | Planees o ajustes fases/herramientas de recon |
| `bug_bounty.md` | Flujo operativo de auditoría | Ejecutes una auditoría end-to-end |
| `scripts_payloads.md` | Scripts y payloads | Escribas scripts o payloads |
| `ctf.md` | Técnicas CTF por categoría | Trabajes retos tipo CTF |

## 🎯 6 Pilares Obligatorios

Cada línea de código debe cumplir:
1. **Coherencia** — código consistente
2. **Congruencia** — specs ↔ implementación ↔ docs alineados
3. **Funcionalidad** — features funcionan exactamente
4. **Estabilidad** — cero crashes, degradación elegante
5. **Seguridad Total** — scope enforcement, payloads no destructivos
6. **Escalabilidad** — arquitectura extensible (tools/agentes pluggables)

## ⚡ Quick Start

```bash
uv sync                              # instalar deps
uv run ruff check code/ tests/       # lint
uv run pytest tests/ -v              # tests
sudo python3 hunter.py -I            # ejecutar (interactivo)
```

## 🚀 Servicios (opcionales, para el cerebro completo)

| Servicio | Puerto | Comando |
|----------|--------|---------|
| Ollama (LLM local + agentes) | 11434 | `ollama serve` |
| Qdrant (RAG) | 6333 | `docker compose up -d qdrant` |

Sin ellos, el cerebro degrada (Gemini / sin RAG) y el CLI sigue funcionando.

## 📖 Referencia Rápida

### Agregar una herramienta de recon
1. Crear `code/recon/tools/nueva_tool.py`
2. Heredar `BaseTool`, definir `name/binary/phase/risk_level`
3. Implementar `run(target, scope)` y `parse_output(raw)`
4. Decorar con `@ToolRegistry.register` (auto-discovery, no se toca el engine)

### Agregar un agente del cerebro
1. Definir `Agent(...)` en `code/brain/agents.py` con rol + modelo + task_types
2. (opcional) modelo override por env `AGENT_*_MODEL`

### Agregar una dependencia
```bash
uv add package-name && uv sync
```

## 🔒 Seguridad Primero

- ✅ Validar scope (`scope.txt`) antes de ejecutar herramientas
- ✅ Secrets en `.env` (NUNCA en código)
- ✅ Payloads no destructivos por defecto
- ✅ El agente propone, el usuario aprueba (riesgo medium+ siempre confirma)
- ✅ Todo registrado en `session.log`

## 🤔 ¿Preguntas?

- `CLAUDE.md` (raíz) — instrucciones maestras
- `code/brain/AGENTS.md`, `code/recon/AGENTS.md` — detalle por módulo
- `PENDIENTES.md` — roadmap
- Memoria en `.claude/projects/.../memory/` — decisiones pasadas

---

**Última actualización:** 30 Septiembre 2026 (reestructuración a CLI)
