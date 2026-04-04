"""
SysMho Hunter - Gestor de Escaneos con PostgreSQL.

Orquesta el ciclo de vida completo de un escaneo
utilizando la base de datos para persistencia y
offloading de lógica pesada.
"""

import asyncio
import uuid
from typing import Any, Optional
from urllib.parse import urlparse

from src.core.recon import ReconEngine
from src.core.analyzer import VulnAnalyzer
from src.core.reporter import ReportGenerator
from src.database.repository import ScanRepository


class ScanManager:
    """Gestor principal de escaneos del agente."""

    def __init__(self) -> None:
        """Inicializa el gestor con los motores necesarios."""
        self.repo = ScanRepository()
        self.recon_engine = ReconEngine()
        self.analyzer = VulnAnalyzer()
        self.reporter = ReportGenerator()
        # Mapa de scan_uid -> scan_id (DB) para tracking rápido
        self._uid_to_id: dict[str, int] = {}

    async def start_scan(
        self,
        target_url: str,
        scope: Optional[list[str]] = None,
        scan_type: str = "full",
    ) -> str:
        """
        Inicia un nuevo escaneo contra un target.

        Args:
            target_url: URL objetivo del escaneo.
            scope: Lista de dominios/IPs permitidos.
            scan_type: Tipo de escaneo (full, recon, fuzz, vuln).

        Returns:
            UID único del escaneo iniciado.

        Raises:
            ValueError: Si el target no es válido.
        """
        # Parsear URL
        parsed = urlparse(target_url)
        hostname = parsed.hostname or target_url

        # Crear/recuperar target en DB
        target_id = await self.repo.upsert_target(
            hostname=hostname,
            base_url=target_url,
            scope=scope,
        )

        # Crear escaneo en DB
        scan_uid = str(uuid.uuid4())[:8]
        scan_id = await self.repo.create_scan(
            scan_uid=scan_uid,
            target_id=target_id,
            scan_type=scan_type,
        )

        self._uid_to_id[scan_uid] = scan_id

        await self.repo.add_log(
            scan_id, "info",
            f"Escaneo {scan_uid} iniciado contra {target_url}",
        )

        # Lanzar escaneo en background
        asyncio.create_task(
            self._run_scan(scan_id, scan_uid, target_url, scan_type, scope)
        )

        return scan_uid

    async def _run_scan(
        self,
        scan_id: int,
        scan_uid: str,
        target_url: str,
        scan_type: str,
        scope: Optional[list[str]] = None,
    ) -> None:
        """Ejecuta el pipeline completo de escaneo con persistencia en DB."""
        try:
            # Fase 1: Reconocimiento
            await self.repo.update_scan_status(scan_id, "recon")
            await self.repo.add_log(
                scan_id, "info", "Fase 1: Iniciando reconocimiento..."
            )

            recon_data = await self.recon_engine.run(
                target=target_url, scope=scope,
            )

            # Guardar datos de recon en DB
            await self.repo.save_recon_data(scan_id, recon_data)
            await self.repo.add_log(
                scan_id, "success",
                f"Reconocimiento completado: "
                f"{len(recon_data.get('ports', []))} puertos, "
                f"{len(recon_data.get('directories', []))} directorios",
            )

            # Fase 2: Análisis de vulnerabilidades
            if scan_type in ("full", "vuln"):
                await self.repo.update_scan_status(scan_id, "analyzing")
                await self.repo.add_log(
                    scan_id, "info",
                    "Fase 2: Analizando vulnerabilidades con IA...",
                )

                findings = await self.analyzer.analyze(
                    target=target_url, recon_data=recon_data,
                )

                # Guardar cada hallazgo en DB
                for finding in findings:
                    await self.repo.add_finding(
                        scan_id=scan_id,
                        finding_type=finding.get("type", "unknown"),
                        title=finding.get("title", "Sin título"),
                        severity=finding.get("severity", "info"),
                        description=finding.get("description"),
                        remediation=finding.get("remediation"),
                        url_affected=finding.get("url_affected"),
                    )

                await self.repo.add_log(
                    scan_id, "success",
                    f"Análisis completado: {len(findings)} hallazgos",
                )

            # Fase 3: Generación de reporte
            await self.repo.update_scan_status(scan_id, "reporting")
            await self.repo.add_log(
                scan_id, "info", "Fase 3: Generando reporte...",
            )

            # Obtener hallazgos de DB para el reporte
            db_findings = await self.repo.get_findings(scan_id)

            report_content = await self.reporter.generate(
                target=target_url,
                findings=db_findings,
                recon_data=recon_data,
            )

            # Guardar reporte en DB
            await self.repo.save_report(
                scan_id=scan_id,
                title=f"Reporte de {target_url}",
                content_md=report_content,
            )

            await self.repo.add_log(
                scan_id, "success", "Reporte generado exitosamente",
            )

            # Finalización
            await self.repo.update_scan_status(scan_id, "completed")
            await self.repo.add_log(
                scan_id, "success", "✅ Escaneo completado exitosamente",
            )

        except Exception as e:
            await self.repo.update_scan_status(
                scan_id, "failed", str(e),
            )
            await self.repo.add_log(
                scan_id, "error", f"Error en escaneo: {str(e)}",
            )

    async def get_status(
        self, scan_uid: str
    ) -> Optional[dict[str, Any]]:
        """Obtiene el estado de un escaneo por su UID."""
        scan = await self.repo.get_scan_by_uid(scan_uid)
        if not scan:
            return None

        scan_id = scan["id"]
        logs_raw = await self.repo.get_recent_logs(scan_id, limit=30)

        # Formatear logs para el frontend
        logs = [
            {
                "timestamp": str(log["created_at"]),
                "level": str(log["level"]),
                "message": log["message"],
            }
            for log in reversed(logs_raw)
        ]

        return {
            "scan_id": scan_uid,
            "status": str(scan["status"]),
            "target_url": scan.get("target_url", ""),
            "started_at": str(scan.get("started_at", "")),
            "finished_at": str(scan.get("finished_at", "")),
            "duration_secs": scan.get("duration_secs"),
            "logs": logs,
        }

    async def get_findings(
        self, scan_uid: str
    ) -> Optional[list[dict[str, Any]]]:
        """Obtiene los hallazgos de un escaneo."""
        scan = await self.repo.get_scan_by_uid(scan_uid)
        if not scan:
            return None

        findings = await self.repo.get_findings(scan["id"])
        return [
            {
                "type": str(f.get("finding_type", "")),
                "title": f.get("title", ""),
                "severity": str(f.get("severity", "info")),
                "description": f.get("description", ""),
                "remediation": f.get("remediation", ""),
                "status": str(f.get("status", "new")),
                "url_affected": f.get("url_affected", ""),
                "is_duplicate": f.get("is_duplicate", False),
            }
            for f in findings
        ]

    async def list_scans(self) -> list[dict[str, Any]]:
        """Lista todos los escaneos registrados."""
        scans = await self.repo.list_scans()
        return [
            {
                "scan_id": s.get("scan_uid", ""),
                "target_url": s.get("target_url", ""),
                "status": str(s.get("status", "")),
                "started_at": str(s.get("started_at", "")),
                "finished_at": str(s.get("finished_at", "")),
                "findings_count": s.get("findings_count", 0),
            }
            for s in scans
        ]

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas globales del dashboard."""
        return await self.repo.get_dashboard_stats()
