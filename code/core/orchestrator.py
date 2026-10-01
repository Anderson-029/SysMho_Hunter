"""
orchestrator — pipeline conversacional: recon → análisis con IA → reporte.

El cerebro propone cada paso y el usuario aprueba antes de que se ejecute
cualquier herramienta que toque el objetivo. Toda la evidencia se guarda en
archivos locales (estilo venom).
"""

import logging

import ui_utils as ui
from brain.router import brain_router
from cli import render
from core.output import SessionOutput
from recon.engine import DEFAULT_PHASES, ReconEngine
from session_logger import log_event

logger = logging.getLogger("hunter")

PHASE_LABELS = {
    "subdomain_enum": "enumeración de subdominios",
    "port_scan": "escaneo de puertos",
    "web_fingerprint": "fingerprint web",
    "crawl": "crawling / descubrimiento de URLs",
    "vuln_scan": "escaneo de vulnerabilidades",
}

RISK_LABELS = {
    "low": "bajo",
    "medium": "medio",
    "high": "alto",
    "critical": "crítico",
}


class Orchestrator:
    def __init__(
        self,
        target: str,
        scope: list[str],
        output: SessionOutput,
        auto_approve: bool = False,
        max_concurrent: int = 5,
    ):
        self.target = target
        self.scope = scope
        self.output = output
        self.auto_approve = auto_approve
        self.engine = ReconEngine(max_concurrent=max_concurrent)

    async def _approval(self, tool, target, scope, phase) -> bool:
        """Callback de aprobación: narra la intención y pide confirmación.

        - Riesgo low: auto-aprobado en modo directo; en interactivo informa.
        - Riesgo medium/high/critical: SIEMPRE pide confirmación explícita.
        """
        risk = getattr(tool, "risk_level", "low")
        risk_es = RISK_LABELS.get(risk, risk)
        label = PHASE_LABELS.get(phase, phase)

        ui.agente(
            f"Propongo correr {ui.BOLD_GREEN}{tool.name}{ui.NC} "
            f"({label}, riesgo {risk_es}) contra {target}."
        )

        if self.auto_approve and risk in ("low", "medium"):
            ui.ok(f"{tool.name}: aprobado automáticamente (modo directo).")
            log_event(
                logger,
                "tool_approved",
                f"{tool.name} auto-aprobado",
                tool=tool.name,
                phase=phase,
                risk=risk,
                mode="auto",
            )
            return True

        aprobado = ui.preguntar(
            f"¿Ejecuto {tool.name}?", default=(risk == "low")
        )
        log_event(
            logger,
            "tool_approved" if aprobado else "tool_rejected",
            f"{tool.name} {'aprobado' if aprobado else 'rechazado'}",
            tool=tool.name,
            phase=phase,
            risk=risk,
            mode="interactive",
        )
        if not aprobado:
            ui.info(f"{tool.name} omitido.")
        return aprobado

    async def run(self, phases: list[str] | None = None) -> dict:
        phases = phases or DEFAULT_PHASES
        ui.agente(
            f"Arranco el reconocimiento de "
            f"{ui.BOLD_GREEN}{self.target}{ui.NC}. "
            "Empiezo por lo pasivo y te voy pidiendo permiso para escalar."
        )
        log_event(
            logger,
            "scan_start",
            f"Inicio de scan contra {self.target}",
            target=self.target,
            scope=self.scope,
            phases=phases,
        )

        all_findings = await self.engine.run_scan(
            target=self.target,
            scope=self.scope,
            phases=phases,
            approval_callback=self._approval,
        )

        # Aplanar findings
        flat: list[dict] = []
        for phase_findings in all_findings.values():
            flat.extend(phase_findings)

        ui.agente(render.spoken_summary(flat))
        log_event(
            logger,
            "recon_done",
            "Recon completado",
            total_findings=len(flat),
            counts=render.summarize_counts(flat),
        )

        # Análisis con el cerebro (best-effort)
        brain_analysis = await self._analyze(flat)

        # Persistir evidencia
        self.output.save_findings(flat)
        report_md = render.build_report(
            self.target, self.scope, flat, brain_analysis
        )
        report_path = self.output.save_report(report_md)

        ui.agente(
            f"Listo. Reporte guardado en {ui.BOLD_GREEN}{report_path}{ui.NC}"
        )
        log_event(
            logger,
            "scan_complete",
            "Scan completado",
            report=str(report_path),
        )
        return {"findings": flat, "report": str(report_path)}

    async def _analyze(self, findings: list[dict]) -> dict | None:
        """Pide al cerebro próximos pasos. Best-effort: si falla, sigue."""
        if not findings:
            return None
        if not ui.preguntar(
            "¿Quieres que analice los hallazgos y sugiera próximos pasos?",
            default=True,
        ):
            return None
        ui.agente("Analizando la superficie con el cerebro híbrido...")
        try:
            result = await brain_router.route(
                "reason_next_steps",
                {
                    "target_url": self.target,
                    "recon_data": {},
                    "findings": findings[:20],
                },
            )
            level = result.get("brain_level", "?")
            model = result.get("model_used", "?")
            if result.get("thought"):
                ui.agente(str(result["thought"]))
            if result.get("command_suggestion"):
                ui.info(f"Siguiente paso: {result['command_suggestion']}")
            ui.info(f"(nivel {level} · {model})")
            log_event(
                logger,
                "brain_analysis",
                "Análisis del cerebro",
                brain_level=level,
                model=model,
            )
            return result
        except Exception as e:
            ui.warn(f"El cerebro no está disponible ahora mismo: {e}")
            logger.warning(f"[Orchestrator] Brain no disponible: {e}")
            return None
