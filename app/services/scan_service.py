"""
SysMho Hunter - Gestor de Escaneos con PostgreSQL.

Orquesta el ciclo de vida completo de un escaneo
utilizando la base de datos para persistencia y
offloading de lógica pesada.
"""

import asyncio
import uuid
import logging
from typing import Any, Optional
from urllib.parse import urlparse

# Nuevos imports modulares
from app.database.repository import ScanRepository
from app.engines.recon_engine import ReconEngine
from app.services.analysis_service import VulnAnalyzer
from app.services.report_service import ReportGenerator

logger = logging.getLogger(__name__)

class ScanService:
    """Orquestador principal del ciclo de vida del escaneo."""

    def __init__(
        self,
        repository: Optional[ScanRepository] = None,
        recon_engine: Optional[ReconEngine] = None,
        analyzer: Optional[VulnAnalyzer] = None,
        reporter: Optional[ReportGenerator] = None
    ) -> None:
        """
        Inicializa el servicio con inyección de dependencias.
        """
        self.repo = repository or ScanRepository()
        self.recon_engine = recon_engine or ReconEngine(repository=self.repo)
        self.analyzer = analyzer or VulnAnalyzer()
        self.reporter = reporter or ReportGenerator()
        self._uid_to_id: dict[str, int] = {}

    async def start_scan(
        self,
        target_url: str,
        scope: Optional[list[str]] = None,
        scan_type: str = "full",
    ) -> str:
        """Inicia un nuevo escaneo."""
        parsed = urlparse(target_url)
        hostname = parsed.hostname or target_url

        # Persistencia inicial
        target_id = await self.repo.upsert_target(hostname, target_url, scope)
        scan_uid = str(uuid.uuid4())[:8]
        scan_id = await self.repo.create_scan(scan_uid, target_id, scan_type)
        
        self._uid_to_id[scan_uid] = scan_id

        await self.repo.add_log(scan_id, "info", f"Escaneo {scan_uid} iniciado contra {target_url}")

        # Dispatch asíncrono
        asyncio.create_task(self._run_pipeline(scan_id, scan_uid, target_url, scan_type, scope))
        
        return scan_uid

    async def _run_pipeline(
        self,
        scan_id: int,
        scan_uid: str,
        target_url: str,
        scan_type: str,
        scope: Optional[list[str]] = None
    ) -> None:
        """Pipeline orquestado de Pentesting."""
        try:
            # Fase 1: Reconocimiento
            await self.repo.update_scan_status(scan_id, "recon")
            recon_data = await self.recon_engine.run_discovery(target_url, scan_id)
            await self.repo.save_recon_data(scan_id, recon_data)

            # Fase 2: Análisis
            findings = []
            if scan_type in ("full", "vuln"):
                await self.repo.update_scan_status(scan_id, "analyzing")
                findings = await self.analyzer.analyze(target_url, recon_data)
                
                for f in findings:
                    await self.repo.add_finding(
                        scan_id=scan_id,
                        finding_type=f.get("type"),
                        title=f.get("title"),
                        severity=f.get("severity"),
                        description=f.get("description"),
                        remediation=f.get("remediation"),
                        url_affected=f.get("url_affected")
                    )

            # Fase 3: Reporte
            await self.repo.update_scan_status(scan_id, "reporting")
            db_findings = await self.repo.get_findings(scan_id)
            report_md = await self.reporter.generate(target_url, db_findings, recon_data)
            
            await self.repo.save_report(scan_id, f"Reporte {scan_uid}", report_md)

            # Finalización
            await self.repo.update_scan_status(scan_id, "completed")
            await self.repo.add_log(scan_id, "success", "Pentesting finalizado exitosamente. ✅")

        except Exception as e:
            logger.exception(f"Falla crítica en escaneo {scan_uid}")
            await self.repo.update_scan_status(scan_id, "failed")
            await self.repo.add_log(scan_id, "error", f"Falla crítica: {str(e)}")

    async def get_status(self, scan_uid: str) -> Optional[dict]:
        """Obtiene estado detallado para el Frontend."""
        scan = await self.repo.get_scan_by_uid(scan_uid)
        if not scan: return None
        
        logs_raw = await self.repo.get_recent_logs(scan["id"], limit=50)
        return {
            "scan_id": scan_uid,
            "status": str(scan["status"]),
            "target_url": scan.get("target_url"),
            "started_at": str(scan.get("started_at")),
            "finished_at": str(scan.get("finished_at")),
            "logs": [{"level": str(l["level"]), "message": l["message"], "time": str(l["created_at"])} for l in reversed(logs_raw)]
        }

    # Métodos delegados al repositorio para mantener la interfaz del frontend
    async def get_findings(self, scan_uid: str):
        scan = await self.repo.get_scan_by_uid(scan_uid)
        return await self.repo.get_findings(scan["id"]) if scan else []

    async def list_scans(self):
        return await self.repo.list_scans()

    async def get_dashboard_stats(self):
        return await self.repo.get_dashboard_stats()
