# PENDIENTES — SysMho Hunter v0.4.0 (CLI)

> Roadmap tras la reestructuración de app web → herramienta CLI.
> Actualizado: 30 Septiembre 2026

---

## ✅ Reestructuración a CLI (COMPLETADA)

- [x] Migrar `brain/`, `rag/`, `recon/` (19 tools) a `code/` — cero acoplamiento a BD
- [x] `config.py` CLI reducido (ollama/qdrant/gemini, sin DB/JWT/web)
- [x] `base_tool.py` sin BD (validación de scope en memoria)
- [x] `engine.py` con aprobación por callback (sin BD)
- [x] Entry point `hunter.py` (modo `-I` + directo)
- [x] `core/scope.py` — scope.txt + confirmación de autorización
- [x] `core/output.py` — evidencia en `output/<target>/<fecha>/`
- [x] `core/orchestrator.py` — pipeline recon → cerebro → reporte
- [x] `cli/render.py` — salida conversacional + report.md en prosa
- [x] Borrada la capa web (frontend, FastAPI, PostgreSQL, Alembic, JWT)
- [x] `pyproject.toml` CLI (sin deps web), `.gitignore`, docs core reescritos
- [x] Scope enforcement validado (dominios, wildcards, CIDRs)

---

## ⏳ Pendiente

### Documentación
- [ ] Reescribir/eliminar las skills `.claude/skills/hunter-*` que referencian
      la API web (9 de ~19 apuntan a endpoints REST / BD)
- [ ] Revisar `.claude/rules/*.md` (refieren puertos/BD/arranque web)
- [ ] `MANUAL.md` completo (guía extendida estilo venom)

### Funcionalidad
- [ ] Smoke test E2E real contra un lab local autorizado
- [ ] Mejorar el reporte: que el cerebro redacte `draft_report` por hallazgo destacado
- [ ] Flag `--mode passive|active|full` como atajo del cerebro (opcional)
- [ ] Reindexar/poblar knowledge base (RAG) con más técnicas

### Calidad
- [ ] Adaptar tests de `tests/` al layout CLI (quitar los de API/auth/BD)
- [ ] `uv run ruff check code/` limpio
- [ ] Cobertura de `core/` (scope, output, orchestrator)

---

## 🔮 Futuro (del roadmap previo, aún válidos)

- [ ] Neo4j — knowledge graph de relaciones entre vulns (tras poblar RAG)
- [ ] Evaluar Qwen 3.5 como LLM local (Nivel 2)
- [ ] Agentes especializados (análisis de API, auth, recon)

---

**Estado general:** núcleo CLI funcional y probado (scope, imports, render).
Falta limpiar skills/rules heredadas de la etapa web y tests.
