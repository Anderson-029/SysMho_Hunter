"""
ScanService — orquesta el pipeline completo de pentesting.
Fases: recon → análisis ML → razonamiento cerebro → reporte
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.brain.ml_engine import ml_engine
from app.brain.router import brain_router
from app.database import AsyncSessionLocal
from app.models.action import PendingAction
from app.models.finding import Finding
from app.models.log import AgentLog, BrainReasoning
from app.models.scan import Scan
from app.models.target import Scope, Target
from app.recon.engine import ReconEngine

logger = logging.getLogger(__name__)

recon_engine = ReconEngine()

# Tools que requieren pending_action antes de ejecutar en modo agresivo
HIGH_RISK_TOOLS = {"sqlmap", "masscan"}


class ScanService:
    async def start_scan(self, scan_id: str, db: AsyncSession) -> None:
        """Lanza el pipeline de scan en background."""
        asyncio.create_task(self._run_pipeline(str(scan_id)))

    async def _run_pipeline(self, scan_id: str) -> None:
        async with AsyncSessionLocal() as db:
            try:
                scan = await db.get(Scan, scan_id)
                if not scan:
                    return

                # Obtener target y scope
                target = await db.get(Target, scan.target_id)
                scope_result = await db.execute(
                    select(Scope).where(
                        Scope.target_id == scan.target_id,
                        Scope.is_in_scope.is_(True),
                    )
                )
                scope_values = [s.value for s in scope_result.scalars().all()]
                target_url = target.name if target else str(scan.target_id)

                await self._log(
                    db,
                    scan_id,
                    "info",
                    "pipeline",
                    f"Iniciando scan {scan_id} contra {target_url}",
                )

                # FASE 1: Reconocimiento
                await self._update_status(db, scan_id, "running", "recon")
                recon_findings = await recon_engine.run_scan(
                    scan_id=scan_id,
                    target=target_url,
                    scope=scope_values or [target_url],
                    db=db,
                    target_id=str(scan.target_id),
                )

                # Guardar hallazgos de recon como findings
                total_recon = 0
                for phase, findings_list in recon_findings.items():
                    for f in findings_list:
                        await self._save_finding(
                            db, scan_id, str(scan.target_id), f
                        )
                        total_recon += 1

                await self._log(
                    db,
                    scan_id,
                    "info",
                    "recon",
                    f"Recon completado: {total_recon} hallazgos"
                    f" en {len(recon_findings)} fases",
                )

                # FASE 2: Análisis ML de findings
                await self._update_status(db, scan_id, "running", "analyzing")
                await self._analyze_findings_with_ml(
                    db, scan_id, str(scan.target_id)
                )

                # FASE 3: Razonamiento del cerebro
                await self._update_status(db, scan_id, "running", "brain")
                brain_result = await brain_router.route(
                    task_type="reason_next_steps",
                    input_data={
                        "target_url": target_url,
                        "recon_data": {"phases": list(recon_findings.keys())},
                        "findings": [],
                        "description": (
                            f"Scan de {target_url}"
                            f" con {total_recon} hallazgos"
                        ),
                    },
                )
                await self._save_brain_reasoning(
                    db, scan_id, "reason_next_steps", brain_result
                )
                await self._log(
                    db,
                    scan_id,
                    "info",
                    "brain",
                    f"Cerebro [{brain_result.get('brain_level')}]"
                    f" → {brain_result.get('action', 'N/A')}",
                )

                # Verificar si el próximo paso requiere aprobación humana
                if brain_result.get("risk_level") in (
                    "high",
                ) or brain_result.get("action") in ("exploit_check",):
                    await self._create_pending_action(
                        db, scan_id, str(scan.target_id), brain_result
                    )
                    await self._log(
                        db,
                        scan_id,
                        "warning",
                        "pipeline",
                        "Acción de alto riesgo pendiente de aprobación:"
                        f" {brain_result.get('action')}",
                    )

                # Finalizar
                await self._update_status(db, scan_id, "completed", None)
                await self._log(
                    db,
                    scan_id,
                    "info",
                    "pipeline",
                    f"✅ Scan {scan_id} completado exitosamente",
                )

            except Exception as e:
                logger.exception(f"Pipeline falló para scan {scan_id}")
                async with AsyncSessionLocal() as db2:
                    await self._update_status(
                        db2, scan_id, "failed", None, error=str(e)
                    )
                    await self._log(
                        db2,
                        scan_id,
                        "error",
                        "pipeline",
                        f"❌ Fallo crítico: {str(e)}",
                    )

    async def _update_status(
        self,
        db: AsyncSession,
        scan_id: str,
        status: str,
        phase: str | None,
        error: str | None = None,
    ) -> None:
        scan = await db.get(Scan, scan_id)
        if scan:
            scan.status = status
            scan.phase = phase
            if status == "completed":
                scan.completed_at = datetime.now(timezone.utc)
            if error:
                scan.error_message = error
            await db.commit()

    async def _log(
        self,
        db: AsyncSession,
        scan_id: str,
        level: str,
        component: str,
        message: str,
    ) -> None:
        log = AgentLog(
            scan_id=scan_id,
            log_level=level,
            component=component,
            message=message,
        )
        db.add(log)
        await db.commit()

        # Broadcast via WebSocket
        from app.websocket.router import broadcast_log

        await broadcast_log(log)

    async def _save_finding(
        self,
        db: AsyncSession,
        scan_id: str,
        target_id: str,
        finding_data: dict,
    ) -> None:
        finding = Finding(
            scan_id=scan_id,
            target_id=target_id,
            title=finding_data.get("title", "Finding sin título"),
            description=finding_data.get("description", ""),
            vuln_type=finding_data.get("type"),
            severity=finding_data.get("severity", "informational"),
            url=finding_data.get("url", ""),
            cwe_id=finding_data.get("cwe_id"),
            cvss_score=finding_data.get("cvss_score"),
            remediation=finding_data.get("remediation"),
        )
        db.add(finding)
        await db.commit()

    async def _analyze_findings_with_ml(
        self, db: AsyncSession, scan_id: str, target_id: str
    ) -> None:
        """Enriquece los findings con predicciones ML."""
        if not ml_engine.is_available:
            return

        result = await db.execute(
            select(Finding).where(
                Finding.scan_id == scan_id, Finding.severity == "informational"
            )
        )
        findings = result.scalars().all()

        for finding in findings:
            desc = f"{finding.title} {finding.description or ''}"
            sev_result = ml_engine.classify_severity(desc)
            finding.ml_severity = sev_result.get("severity")
            finding.ml_confidence = sev_result.get("confidence")

        await db.commit()
        await self._log(
            db,
            scan_id,
            "info",
            "ml",
            f"ML enriqueció {len(findings)} findings",
        )

    async def _save_brain_reasoning(
        self, db: AsyncSession, scan_id: str, task_type: str, result: dict
    ) -> None:
        reasoning = BrainReasoning(
            scan_id=scan_id,
            task_type=task_type,
            brain_level=result.get("brain_level", 0),
            model_used=result.get("model_used"),
            output_data=result,
            confidence=result.get("confidence"),
            reasoning_text=result.get("thought"),
            latency_ms=result.get("total_latency_ms"),
        )
        db.add(reasoning)
        await db.commit()

    async def _create_pending_action(
        self,
        db: AsyncSession,
        scan_id: str,
        target_id: str,
        brain_result: dict,
    ) -> None:
        action = PendingAction(
            action_type="exploit_check",
            description=(
                "El cerebro sugiere: "
                f"{brain_result.get('command_suggestion', 'N/A')}"
            ),
            scan_id=scan_id,
            target_id=target_id,
            payload=brain_result,
            risk_level=brain_result.get("risk_level", "high"),
            risk_reason=brain_result.get("thought", ""),
            requested_by="agent",
        )
        db.add(action)
        await db.commit()


scan_service = ScanService()
