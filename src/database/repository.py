"""
SysMho Hunter - Repositorio de base de datos.

Capa de acceso a datos que encapsula las llamadas a las
funciones almacenadas de PostgreSQL, manteniendo la lógica
pesada en la base de datos.
"""

import json
from typing import Any, Optional

from src.database.connection import db


class ScanRepository:
    """Repositorio para operaciones de escaneos."""

    async def upsert_target(
        self,
        hostname: str,
        base_url: str,
        ip_address: Optional[str] = None,
        scope: Optional[list[str]] = None,
    ) -> int:
        """
        Crea o actualiza un target en la base de datos.

        Args:
            hostname: Nombre del host.
            base_url: URL base del target.
            ip_address: Dirección IP opcional.
            scope: Lista de dominios en scope.

        Returns:
            ID del target.
        """
        scope_json = json.dumps(scope or [])
        return await db.fetch_val(
            "SELECT fn_upsert_target($1, $2, $3, $4::JSONB)",
            hostname, base_url, ip_address, scope_json,
        )

    async def create_scan(
        self,
        scan_uid: str,
        target_id: int,
        scan_type: str = "full",
        config: Optional[dict] = None,
    ) -> int:
        """
        Crea un nuevo escaneo.

        Args:
            scan_uid: Identificador único del escaneo.
            target_id: ID del target.
            scan_type: Tipo de escaneo.
            config: Configuración del escaneo.

        Returns:
            ID del escaneo creado.
        """
        config_json = json.dumps(config or {})
        return await db.fetch_val(
            "SELECT fn_create_scan($1, $2, $3, $4::JSONB)",
            scan_uid, target_id, scan_type, config_json,
        )

    async def update_scan_status(
        self,
        scan_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Actualiza el estado de un escaneo."""
        await db.execute(
            "SELECT fn_update_scan_status($1, $2::scan_status, $3)",
            scan_id, status, error_message,
        )

    async def save_recon_data(
        self, scan_id: int, recon_data: dict
    ) -> None:
        """Guarda los datos de reconocimiento."""
        await db.execute(
            "SELECT fn_save_recon_data($1, $2::JSONB)",
            scan_id, json.dumps(recon_data),
        )

    async def add_finding(
        self,
        scan_id: int,
        finding_type: str,
        title: str,
        severity: str,
        description: Optional[str] = None,
        remediation: Optional[str] = None,
        evidence: Optional[dict] = None,
        url_affected: Optional[str] = None,
        cvss_score: Optional[float] = None,
    ) -> int:
        """Agrega un hallazgo a la base de datos."""
        evidence_json = json.dumps(evidence or {})
        return await db.fetch_val(
            "SELECT fn_add_finding("
            "$1, $2, $3, $4::severity_level, $5, $6, "
            "$7::JSONB, $8, $9::DECIMAL"
            ")",
            scan_id, finding_type, title, severity,
            description, remediation, evidence_json,
            url_affected, cvss_score,
        )

    async def add_log(
        self,
        scan_id: int,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> int:
        """Agrega un log de escaneo."""
        metadata_json = json.dumps(metadata or {})
        return await db.fetch_val(
            "SELECT fn_add_log($1, $2::log_level, $3, $4::JSONB)",
            scan_id, level, message, metadata_json,
        )

    async def get_scan_summary(
        self, scan_id: int
    ) -> Optional[dict[str, Any]]:
        """Obtiene el resumen de un escaneo."""
        row = await db.fetch_one(
            "SELECT * FROM fn_get_scan_summary($1)", scan_id
        )
        if row:
            return dict(row)
        return None

    async def get_scan_by_uid(
        self, scan_uid: str
    ) -> Optional[dict[str, Any]]:
        """Obtiene un escaneo por su UID."""
        row = await db.fetch_one(
            "SELECT s.*, t.base_url as target_url "
            "FROM scans s "
            "JOIN targets t ON s.target_id = t.id "
            "WHERE s.scan_uid = $1",
            scan_uid,
        )
        if row:
            return dict(row)
        return None

    async def get_recent_logs(
        self, scan_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Obtiene los últimos logs de un escaneo."""
        rows = await db.fetch_all(
            "SELECT * FROM fn_get_recent_logs($1, $2)",
            scan_id, limit,
        )
        return [dict(r) for r in rows]

    async def get_findings(
        self, scan_id: int
    ) -> list[dict[str, Any]]:
        """Obtiene los hallazgos de un escaneo."""
        rows = await db.fetch_all(
            "SELECT * FROM findings "
            "WHERE scan_id = $1 "
            "ORDER BY "
            "  CASE severity "
            "    WHEN 'critical' THEN 0 "
            "    WHEN 'high' THEN 1 "
            "    WHEN 'medium' THEN 2 "
            "    WHEN 'low' THEN 3 "
            "    ELSE 4 "
            "  END, created_at DESC",
            scan_id,
        )
        return [dict(r) for r in rows]

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Obtiene las estadísticas globales."""
        row = await db.fetch_one(
            "SELECT * FROM fn_get_dashboard_stats()"
        )
        if row:
            return dict(row)
        return {}

    async def list_scans(
        self, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Lista los escaneos más recientes."""
        rows = await db.fetch_all(
            "SELECT s.id, s.scan_uid, s.scan_type, s.status, "
            "s.started_at, s.finished_at, s.duration_secs, "
            "t.base_url as target_url, t.hostname, "
            "(SELECT COUNT(*) FROM findings f WHERE f.scan_id = s.id) "
            "as findings_count "
            "FROM scans s "
            "JOIN targets t ON s.target_id = t.id "
            "ORDER BY s.created_at DESC "
            "LIMIT $1",
            limit,
        )
        return [dict(r) for r in rows]

    async def save_report(
        self,
        scan_id: int,
        title: str,
        content_md: str,
        platform: Optional[str] = None,
    ) -> int:
        """Guarda un reporte generado."""
        return await db.fetch_val(
            "SELECT fn_save_report($1, $2, $3, $4)",
            scan_id, title, content_md, platform,
        )

    async def get_config(self, key: str) -> Optional[str]:
        """Obtiene un valor de configuración del agente."""
        return await db.fetch_val(
            "SELECT value FROM agent_config WHERE key = $1",
            key,
        )
