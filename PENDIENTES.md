# PENDIENTES — SysMho Hunter v0.4.0 (CLI)

> Roadmap tras la reestructuración de app web → herramienta CLI.
> Actualizado: 30 Septiembre 2026

---

## ✅ Completado

### Reestructuración a CLI
- [x] Migrar `brain/`, `rag/`, `recon/` (19 tools) a `code/` — cero acoplamiento a BD
- [x] `config.py` CLI reducido; `base_tool.py`/`engine.py` sin BD (scope en memoria)
- [x] Entry point `hunter.py` (modo `-I` + directo)
- [x] `core/scope.py` (scope.txt + confirmación), `core/output.py`, `core/orchestrator.py`
- [x] `cli/render.py` — salida conversacional + report.md en prosa
- [x] Borrada la capa web (frontend, FastAPI, PostgreSQL, Alembic, JWT)
- [x] `pyproject.toml` CLI, `.gitignore`, scope enforcement validado

### Cerebro — agentes especializados (multi-modelo Ollama)
- [x] `brain/agents.py` — ReconAnalyzer, CodeAnalyzer, ReportWriter, PayloadCrafter
- [x] `brain/local_llm.py` — multi-modelo (/api/chat), degrada si el modelo falta
- [x] `router.py` resuelve agente por `task_type` en el Nivel 2
- [x] Modelos configurables por env (`AGENT_*_MODEL`)
- [x] Flujo `craft_payload` activado (opt-in, bajo aprobación, `payloads.md`)

### Limpieza y docs
- [x] Borradas skills web (`.claude/skills/`)
- [x] `.claude/rules/` limpiado al estado CLI (sin web/BD/HackerOne)
- [x] Docs raíz unificados: README, CLAUDE, SECURITY, PENDIENTES; AGENTS de code/
- [x] Reencuadre: 0 menciones a HackerOne; sin atribución a Claude en commits
- [x] tests/ saneados (scope 9/9), `ruff check` limpio
- [x] codebase-memory-mcp: server global único (`~/.local/bin/codebase-memory-mcp`)
      sirviendo todos los proyectos desde `~/.cache/codebase-memory-mcp/`; Hunter
      indexado (611 nodos / 1868 edges); `.codebase-memory/` local eliminada y
      gitignoreada (el grafo no se versiona en el repo)

---

## ⏳ Pendiente

### Funcionalidad
- [ ] Smoke test E2E real contra un lab local autorizado
- [ ] `draft_report` por hallazgo destacado (ReportWriter) dentro del reporte
- [ ] Flag `--mode passive|active|full` como atajo (opcional)
- [ ] Reindexar/poblar knowledge base (RAG) con más técnicas

### Calidad
- [ ] Tests para `core/` (scope, output, orchestrator) y para agents/craft_payload
- [ ] Cobertura y, opcional, CI local

### Documentación
- [ ] `MANUAL.md` completo (guía extendida estilo venom)
- [ ] Re-indexar el grafo del MCP (`codebase-memory-mcp cli index_repository`)
      cuando cambie el código de forma relevante

---

## 🔮 Futuro

- [ ] Neo4j — knowledge graph de relaciones entre vulns (tras poblar RAG)
- [ ] Más roles de agente según haga falta (p. ej. AuthAnalyzer)

---

**Estado general:** CLI funcional, con agentes especializados y crafteo de
payloads activos. `ruff` limpio, scope tests en verde. Falta smoke test E2E
real y ampliar la cobertura de tests.
