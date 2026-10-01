# Security Policy — SysMho Hunter

SysMho Hunter es una herramienta de pentesting para **auditorías autorizadas**.
Su diseño prioriza que nunca opere fuera de alcance ni ejecute acciones
destructivas sin confirmación.

---

## Scope Enforcement (salvaguarda central)

Antes de ejecutar cualquier herramienta contra un objetivo:

1. Los objetivos vienen SIEMPRE de `scope.txt` (dominios, `*.wildcards`, IPs, CIDRs).
   Nunca se hardcodean en el código.
2. `BaseTool._validate_scope()` valida el objetivo contra el scope cargado.
   Un objetivo fuera de scope aborta la operación (`ScopeViolationError`).
3. Al iniciar, el usuario confirma explícitamente que tiene autorización.
   La confirmación queda registrada en `session.log`.

> El scope enforcement es una salvaguarda técnica, **no** un sustituto de tu
> responsabilidad legal. Solo tú garantizas que tienes permiso por escrito.

---

## Aprobación de Operaciones

- El agente **propone** cada herramienta; el usuario **aprueba** antes de que
  se ejecute.
- Riesgo `low`: puede auto-aprobarse en modo directo (`--yes`).
- Riesgo `medium`/`high`/`critical`: **siempre** requiere confirmación explícita.
- Toda aprobación/rechazo se registra en `session.log` (JSON estructurado).

---

## Payloads

- Por defecto, no destructivos: sqlmap con `--level=1 --risk=1`.
- Flags agresivos o destructivos requieren confirmación explícita del usuario.
- Cada herramienta ejecutada se registra con su comando en la evidencia.

---

## Secretos

- `GEMINI_API_KEY` y cualquier credencial viven en `.env` (gitignored).
- `.env.example` es la plantilla, sin valores reales.
- Nunca commitear `.env`. Si se expone una clave (p. ej. pegada en un chat),
  rotarla.

---

## Auditoría

- `session.log` por sesión: autorización, decisiones del cerebro, herramientas
  ejecutadas, aprobaciones. Formato JSON con timestamps ISO8601.
- `findings.json` + `recon/` conservan la evidencia cruda para revisión.

---

## Divulgación de Vulnerabilidades (del propio Hunter)

Si encuentras una vulnerabilidad en SysMho Hunter, no la publiques; repórtala
en privado al autor con pasos de reproducción.

---

**Alcance:** herramienta de uso autorizado. El uso contra sistemas de terceros
sin permiso es ilegal y es responsabilidad exclusiva del operador.
