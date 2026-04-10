# AGENTS.md — backend/app/recon/

## Arquitectura

```
ReconEngine.run_scan(scan_id, target, scope, phases)
    │
    ├── ToolRegistry.get_tools_for_phase("subdomain_enum")  → subfinder, amass
    ├── ToolRegistry.get_tools_for_phase("port_scan")       → nmap, masscan
    ├── ToolRegistry.get_tools_for_phase("web_fingerprint") → whatweb, wafw00f, httprobe, eyewitness
    ├── ToolRegistry.get_tools_for_phase("crawl")           → hakrawler, gau, waybackurls
    ├── ToolRegistry.get_tools_for_phase("vuln_scan")       → nuclei, nikto, dalfox, ffuf, feroxbuster, gobuster, wfuzz
    └── ToolRegistry.get_tools_for_phase("exploit")         → sqlmap (critical → pending_action)
```

Concurrencia máxima: `recon.max_concurrent_tools` de `agent_config` (default: 5).

## Patrón para agregar una nueva herramienta

1. Crear `backend/app/recon/tools/nueva_tool.py`
2. Heredar de `BaseTool`
3. Definir `name`, `binary`, `phase`, `risk_level`
4. Implementar `run()` y `parse_output()`
5. Decorar con `@ToolRegistry.register`
6. La tool aparece automáticamente en el registro al importar el módulo

## Reglas CRÍTICAS

- `_validate_scope(target, scope)` se llama SIEMPRE antes de ejecutar. Si falla → `ScopeViolationError` (loggeada en `agent_logs`)
- `risk_level=high/critical` → crear `pending_action` en BD y NO ejecutar hasta aprobación humana via `/hunter-actions`
- Timeout por defecto: 300s (`recon.default_timeout` en agent_config). Herramientas lentas (amass, masscan): 600s
- Usar `asyncio.create_subprocess_exec`, nunca `subprocess.run` síncrono
- El comando exacto ejecutado se guarda en `scan_tasks.command` (sin secrets, sin tokens)
- stdout/stderr completos se guardan en `scan_tasks.stdout/stderr`

## Tools por Fase

| Fase | Tools | Risk Level |
|------|-------|-----------|
| subdomain_enum | subfinder, amass | low |
| port_scan | nmap, masscan | medium |
| web_fingerprint | whatweb, wafw00f, httprobe, eyewitness | low |
| crawl | hakrawler, gau, waybackurls | low |
| vuln_scan | nuclei, nikto, ffuf, feroxbuster, gobuster, wfuzz, dalfox | medium |
| exploit | sqlmap (nivel agresivo) | critical → pending_action |

## Excepciones del BaseTool

| Excepción | Cuándo | Efecto |
|-----------|--------|--------|
| `ScopeViolationError` | Target fuera del scope autorizado | Cancela la task, logea en agent_logs |
| `ToolNotInstalledError` | Binary no encontrado en PATH | Marca scan_task como skipped |
| `ToolTimeoutError` | Excede timeout configurado | Marca scan_task como timeout, continúa pipeline |

## Verificar Arsenal

Ejecutar `/hunter-recon` para ver herramientas instaladas vs pendientes.
Instalar todas con: `bash scripts/install_tools.sh`
