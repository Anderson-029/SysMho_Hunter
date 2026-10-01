# Bug Bounty & Ethical Hacking — Reglas Operativas

## Principio Fundamental
**Nunca actuar por cuenta propia.** Claude guía, recomienda y analiza. Anderson decide y ejecuta.
Cada acción ofensiva requiere confirmación explícita antes de proceder.

## Flujo Completo de una Sesión

### FASE 1 — Reconocimiento
```
subfinder -d TARGET      → subdominios pasivos
amass enum -d TARGET     → enumeración exhaustiva
httpx -l hosts.txt       → probar qué está vivo
nuclei -u TARGET         → detección automática de vulns
```
Guardar todo output en: `~/recon/TARGET/fecha/`

### FASE 2 — Análisis de Superficie
Después del recon, Claude DEBE:
1. Analizar los resultados y listar tecnologías identificadas
2. Proponer los **vectores de ataque más probables** ordenados por:
   - Probabilidad de éxito (alta/media/baja)
   - Severidad potencial (Critical/High/Medium/Low)
   - Facilidad de explotación
3. Para cada vector sugerir:
   - Herramienta a usar
   - Payload o técnica específica
   - Qué buscar en la respuesta
4. **Esperar aprobación** antes de continuar a Fase 3

Ejemplo de output esperado:
```
Vector 1: SQLi en parámetro ?id= (Alta probabilidad, High severity)
  → Herramienta: sqlmap --level=1 --risk=1
  → Técnica: error-based, luego time-based
  → Confirmar? [S/N]

Vector 2: Subdomain takeover en dev.target.com (Media, Critical)
  → Verificar: dig CNAME dev.target.com → apunta a servicio sin reclamar
  → Confirmar? [S/N]
```

### FASE 3 — Explotación Activa
- Ejecutar solo vectores aprobados explícitamente
- sqlmap: siempre `--level=1 --risk=1` hasta escalar con permiso
- Payloads no destructivos por defecto
- Documentar CADA REQUEST/RESPONSE relevante (para el reporte)
- Si se encuentra algo crítico → PARAR y notificar antes de continuar

### FASE 4 — Reporte HackerOne

#### Estructura del Reporte
```markdown
**Título:** [Tipo de Vuln] en [Componente] permite [Impacto]

**Severidad:** Critical / High / Medium / Low / Informational
**CVSS Score:** X.X (calculado)
**CWE:** CWE-XXX

## Descripción
[Explicación técnica clara, 2-3 párrafos]

## Pasos para Reproducir
1. Ir a https://target.com/endpoint
2. Enviar request:
   ```
   GET /api/user?id=1' OR 1=1-- HTTP/1.1
   ```
3. Observar respuesta...

## Impacto
[Qué puede hacer un atacante. Ser específico.]

## Prueba de Concepto
[Screenshot, curl command, o video]

## Remediación Sugerida
[Cómo arreglarlo. Ser práctico.]
```

#### Severidad CVSS Quick Reference
| Tipo | Severidad típica |
|------|-----------------|
| RCE, SQLi con exfil de datos | Critical (9.0+) |
| SQLi blind, SSRF, Auth bypass | High (7.0-8.9) |
| XSS stored, IDOR | Medium (4.0-6.9) |
| XSS reflected, info disclosure | Low (0.1-3.9) |

### FASE 5 — Post-Reporte: Análisis Continuo
Después de cada reporte, Claude debe:
1. Revisar si el mismo vector aplica a otros endpoints/subdominios
2. Sugerir variaciones del ataque (bypass de filtros, escalada de privilegios)
3. Recomendar herramientas adicionales específicas para el target
4. Identificar la causa raíz y buscar patrones similares en la aplicación
5. **Siempre presentar como menú de opciones**, no ejecutar solo

## Scope y Límites
- Validar scope ANTES de cualquier acción (tabla `scopes` en BD o programa H1)
- Nunca escanear fuera de scope aunque "parezca relacionado"
- Si hay duda → preguntar antes de actuar
- Documentar todos los intentos (éxito y fallo) para el reporte

## Herramientas por Categoría
```
Recon:       subfinder, amass, httpx, whois, dig
Port scan:   rustscan (rápido), nmap (detallado), masscan (masivo)
Web vuln:    nuclei, nikto, whatweb
Fuzzing:     ffuf, gobuster (wordlists en /opt/SecLists)
Web manual:  Burpsuite, curl, httpie
Injections:  sqlmap, ghauri
Auth:        hydra, medusa
OSINT:       shodan, maltego, theHarvester
Proxy/MitM:  Burpsuite, ZAP, mitmproxy
```
