# AGENTS.md — code/recon/

## Arquitectura

```
ReconEngine.run_scan(target, scope, phases, approval_callback)
    │
    ├── get_tools_for_phase("subdomain_enum")  → subfinder, amass
    ├── get_tools_for_phase("port_scan")       → nmap, masscan
    ├── get_tools_for_phase("web_fingerprint") → whatweb, wafw00f, httprobe, eyewitness
    ├── get_tools_for_phase("crawl")           → hakrawler, gau, waybackurls
    └── get_tools_for_phase("vuln_scan")       → nuclei, nikto, dalfox, ffuf, feroxbuster, gobuster, wfuzz, sqlmap
```

Por cada fase: se pide aprobación de cada herramienta vía `approval_callback`
(confirmación interactiva en terminal), y las aprobadas se ejecutan en paralelo
respetando el semáforo de concurrencia (`max_concurrent`, default 5).

## Scope enforcement (crítico)

Antes de ejecutar, `BaseTool.safe_run()` llama a `_validate_scope(target, scope)`:
valida el objetivo contra la lista cargada de `scope.txt` (dominios, `*.wildcards`,
IPs, CIDRs). Fuera de scope → `ScopeViolationError`. Nunca se hardcodean objetivos.

## Patrón para agregar una nueva herramienta

1. Crear `code/recon/tools/nueva_tool.py`
2. Heredar de `BaseTool`
3. Definir `name`, `binary`, `phase`, `risk_level` (low|medium|high|critical)
4. Implementar `run(target, scope, **kwargs)` y `parse_output(raw_output)`
5. Decorar la clase con `@ToolRegistry.register`
6. La tool se auto-descubre al importar `recon.tools` (no hay que tocar el engine)

## Riesgo y aprobación

- `risk_level` define si la herramienta requiere confirmación explícita.
- `low` puede auto-aprobarse en modo directo (`--yes`).
- `medium`/`high`/`critical` SIEMPRE piden confirmación (lo gestiona el
  orquestador, no la herramienta).
- Payloads no destructivos por defecto (ej. sqlmap `--level=1 --risk=1`).

## Archivos

| Archivo | Responsabilidad |
|---------|-----------------|
| `engine.py` | ReconEngine: orquesta fases, aplica approval_callback, concurrencia |
| `base_tool.py` | BaseTool (ABC): scope validation, subprocess async, safe_run |
| `tool_registry.py` | ToolRegistry: registro + auto-discovery de tools |
| `tool_explanations.py` | Texto humano por herramienta |
| `tools/*.py` | 19 wrappers de herramientas CLI |

## Notas de diseño

- **Sin base de datos.** Si una herramienta no está instalada, su `scan_task`
  se omite (`ToolNotInstalledError` capturado) y el pipeline continúa.
- **Timeout** por herramienta vía `asyncio.wait_for` (default 300s).
