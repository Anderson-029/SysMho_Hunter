"""
render — construye la salida conversacional (prosa) y el reporte markdown.

El objetivo es que los hallazgos se presenten como lo haría un analista
hablándote, no como tablas o JSON crudo.
"""

from datetime import datetime

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "informational": 4,
}


def sort_findings(findings: list[dict]) -> list[dict]:
    return sorted(
        findings,
        key=lambda f: SEVERITY_ORDER.get(
            str(f.get("severity", "informational")).lower(), 5
        ),
    )


def summarize_counts(findings: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        sev = str(f.get("severity", "informational")).lower()
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def spoken_summary(findings: list[dict]) -> str:
    """Resumen en una/dos frases, en voz del agente."""
    if not findings:
        return (
            "No encontré nada reseñable en esta pasada. Puede que el "
            "objetivo esté bien protegido o que haga falta escalar el modo."
        )
    counts = summarize_counts(findings)
    relevantes = [
        (sev, counts[sev])
        for sev in ("critical", "high", "medium")
        if sev in counts
    ]
    total = len(findings)
    if relevantes:
        partes = ", ".join(f"{n} {sev}" for sev, n in relevantes)
        return (
            f"Reuní {total} hallazgos. Lo que vale la pena mirar: {partes}. "
            "Te detallo lo importante abajo."
        )
    return (
        f"Reuní {total} hallazgos, todos de severidad baja o informativa "
        "(sobre todo superficie de ataque: subdominios, puertos, tecnologías)."
    )


def build_report(
    target: str,
    scope: list[str],
    findings: list[dict],
    brain_analysis: dict | None = None,
) -> str:
    """Genera report.md en prosa conversacional."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ordered = sort_findings(findings)
    counts = summarize_counts(findings)

    lines: list[str] = []
    lines.append(f"# Reporte de pentesting — {target}")
    lines.append("")
    lines.append(f"> Generado por SysMho Hunter · {ts}")
    lines.append(f"> Scope autorizado: {', '.join(scope)}")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    lines.append(spoken_summary(findings))
    lines.append("")
    if counts:
        resumen = " · ".join(
            f"**{sev}**: {n}"
            for sev, n in sorted(
                counts.items(),
                key=lambda kv: SEVERITY_ORDER.get(kv[0], 5),
            )
        )
        lines.append(resumen)
        lines.append("")

    if brain_analysis and brain_analysis.get("thought"):
        lines.append("## Análisis del agente")
        lines.append("")
        lines.append(str(brain_analysis["thought"]))
        if brain_analysis.get("command_suggestion"):
            lines.append("")
            lines.append(
                f"**Siguiente paso sugerido:** "
                f"{brain_analysis['command_suggestion']}"
            )
        lines.append("")

    destacados = [
        f
        for f in ordered
        if str(f.get("severity", "")).lower() in ("critical", "high", "medium")
    ]
    if destacados:
        lines.append("## Hallazgos destacados")
        lines.append("")
        for f in destacados:
            sev = str(f.get("severity", "")).upper()
            title = f.get("title", f.get("type", "Hallazgo"))
            lines.append(f"### [{sev}] {title}")
            if f.get("url"):
                lines.append(f"- **Ubicación:** {f['url']}")
            if f.get("description"):
                lines.append(f"- {f['description']}")
            lines.append("")

    # Superficie (informativos) resumida, no exhaustiva en prosa
    superficie = [
        f
        for f in ordered
        if str(f.get("severity", "")).lower() in ("low", "informational")
    ]
    if superficie:
        lines.append("## Superficie de ataque (informativo)")
        lines.append("")
        lines.append(
            f"Se registraron {len(superficie)} elementos de superficie "
            "(subdominios, puertos, tecnologías). Detalle completo en "
            "`findings.json` y `recon/`."
        )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Evidencia cruda por herramienta en `recon/`. Ciclo de vida de la "
        "sesión en `session.log`._"
    )
    return "\n".join(lines)
