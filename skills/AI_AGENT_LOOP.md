# Skill: AI Agent Loop — Razonamiento Táctico con LLM

Eres experto en diseñar agentes de IA que razonan, actúan y aprenden en ciclos. Aplicas ReAct (Reason + Act), cadenas de pensamiento y decisiones condicionales.

## El Loop ReAct para Pentesting

```
OBSERVE → THINK → ACT → OBSERVE → THINK → ACT → ...
```

### Ciclo Completo
```python
async def agent_loop(scan_context: ScanContext) -> List[Finding]:
    max_iterations = 10
    findings = []
    
    for i in range(max_iterations):
        # OBSERVE: estado actual
        observation = build_observation(scan_context, findings)
        
        # THINK: razonar con LLM
        thought = await llm.reason(
            system=PENTESTING_SYSTEM_PROMPT,
            observation=observation,
            history=scan_context.action_history
        )
        
        # DECIDE: ¿continuar, explotar, o terminar?
        if thought.action == "FINISH":
            break
        if thought.requires_approval:
            await request_human_approval(thought)
            continue
            
        # ACT: ejecutar herramienta
        result = await execute_tool(thought.action, thought.params)
        
        # UPDATE: actualizar contexto
        scan_context.action_history.append({
            "thought": thought.reasoning,
            "action": thought.action,
            "result": result.summary
        })
        findings.extend(result.new_findings)
    
    return findings
```

## System Prompt para el Agente
```
Eres un bug bounty hunter experto. Dado el estado actual de un escaneo,
decides el siguiente paso más inteligente para encontrar vulnerabilidades.

Responde SIEMPRE en JSON con esta estructura:
{
  "reasoning": "Por qué tomo esta decisión",
  "action": "TOOL_NAME | FINISH | REQUEST_APPROVAL",
  "params": { ... },
  "priority": 1-10,
  "requires_approval": false,
  "expected_outcome": "Qué espero encontrar"
}

Herramientas disponibles: subfinder, httpx, ffuf, nuclei, dalfox, arjun, gau
```

## Encadenamiento de Vulnerabilidades
El agente debe buscar cadenas, no bugs aislados:
- `Info Disclosure` → `IDOR` → `PII Access` = High/Critical
- `Open Redirect` + `OAuth` = Account Takeover
- `SSRF interno` + `metadata cloud` = Critical RCE equivalente
- `XSS stored` + `admin panel` = Privilege Escalation

## Memoria del Agente (Context Window)
```python
class AgentMemory:
    recon_data: ReconResult
    findings_so_far: List[Finding]
    tested_endpoints: Set[str]     # evitar redundancia
    failed_attempts: List[str]     # no repetir lo que no funcionó
    action_history: List[Action]   # últimas N acciones
    session_goals: List[str]       # objetivos de la sesión
```

## Herramientas que el Agente puede llamar
```python
TOOL_REGISTRY = {
    "subfinder":  SubfinderTool,
    "httpx":      HttpxTool,
    "ffuf":       FfufTool,
    "nuclei":     NucleiTool,
    "dalfox":     DalfoxTool,      # XSS hunter
    "sqlmap":     SqlmapTool,      # SQLi (requiere aprobación)
    "arjun":      ArjunTool,       # param discovery
    "gau":        GauTool,         # historical URLs
    "http_probe": HttpProbeTool,   # custom requests
}
```

## Reglas de Seguridad del Agente
1. NUNCA ejecutar payloads destructivos sin aprobación humana
2. SIEMPRE validar que el target está en scope antes de cada acción
3. PAUSAR si rate limit detectado (429 o bloqueo de IP)
4. NUNCA exfiltrar datos reales de la víctima (solo PoC minimal)
5. REGISTRAR todas las acciones en la BD para auditoría
