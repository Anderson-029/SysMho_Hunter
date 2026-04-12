"""
ReconEngine — orquesta la ejecución de herramientas por fases.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.recon.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

DEFAULT_PHASES = [
    "subdomain_enum",
    "port_scan",
    "web_fingerprint",
    "crawl",
    "vuln_scan",
]

# Tipo del callback de aprobación
ApprovalCallback = Callable[
    [Any, str, list[str], str, str, AsyncSession],
    Coroutine[Any, Any, bool],
]


class ReconEngine:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def run_scan(
        self,
        scan_id: str,
        target: str,
        scope: list[str],
        phases: list[str] | None = None,
        db: AsyncSession | None = None,
        target_id: str | None = None,
        approval_callback: ApprovalCallback | None = None,
    ) -> dict:
        """
        Ejecuta todas las fases de reconocimiento en orden.
        Retorna un dict con los findings agrupados por fase.

        target_id: UUID del target en BD (para validación mejorada)
        approval_callback: función async que solicita aprobación humana
            antes de ejecutar cada herramienta. Si retorna False, la
            herramienta se salta.
        """
        phases = phases or DEFAULT_PHASES
        all_findings: dict[str, list[dict]] = {}

        for phase in phases:
            tools = ToolRegistry.get_tools_for_phase(phase)
            if not tools:
                logger.info(
                    f"[Recon] Fase '{phase}': sin tools instaladas, saltando."
                )
                continue

            logger.info(
                f"[Recon] Fase '{phase}': {len(tools)} tools disponibles."
            )
            phase_findings = await self._run_phase(
                tools,
                target,
                scope,
                phase,
                target_id,
                db,
                approval_callback,
            )
            all_findings[phase] = phase_findings

        return all_findings

    async def _run_phase(
        self,
        tools: list,
        target: str,
        scope: list[str],
        phase: str,
        target_id: str | None = None,
        db: AsyncSession | None = None,
        approval_callback: ApprovalCallback | None = None,
    ) -> list[dict]:
        """Ejecuta las tools de una fase, una a una para que el usuario
        pueda aprobar o rechazar cada una antes de que empiece.

        Las herramientas aprobadas se ejecutan en paralelo respetando
        el semáforo de concurrencia.
        """
        # Fase A: solicitar aprobación secuencialmente (una a la vez)
        approved_tools = []
        if approval_callback and db and target_id:
            for tool in tools:
                ok = await approval_callback(
                    tool, target, scope, phase, target_id, db
                )
                if ok:
                    approved_tools.append(tool)
        else:
            # Sin callback → ejecutar todas (compatibilidad hacia atrás)
            approved_tools = tools

        if not approved_tools:
            return []

        # Fase B: ejecutar las herramientas aprobadas en paralelo
        tasks = [
            self._run_tool(tool, target, scope, target_id, db)
            for tool in approved_tools
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings = []
        for tool, result in zip(approved_tools, results):
            if isinstance(result, Exception):
                logger.warning(
                    f"[Recon] {tool.name}: {type(result).__name__}: {result}"
                )
                continue
            findings.extend(result.parsed_findings)
            n = len(result.parsed_findings)
            logger.info(
                f"[Recon] {tool.name}: {n} findings"
                f" ({result.execution_time_ms}ms)"
            )

        return findings

    async def _run_tool(
        self,
        tool,
        target: str,
        scope: list[str],
        target_id: str | None = None,
        db: AsyncSession | None = None,
    ):
        async with self._semaphore:
            return await tool.safe_run(
                target, scope, target_id=target_id, db=db
            )

    def get_arsenal_status(self) -> dict:
        """Retorna estado de todas las herramientas registradas."""
        return ToolRegistry.all_tools_status()
