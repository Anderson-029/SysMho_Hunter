"""
ReconEngine — orquesta la ejecución de herramientas por fases.
"""

import asyncio
import logging

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
    ) -> dict:
        """
        Ejecuta todas las fases de reconocimiento en orden.
        Retorna un dict con los findings agrupados por fase.
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
            phase_findings = await self._run_phase(tools, target, scope, phase)
            all_findings[phase] = phase_findings

        return all_findings

    async def _run_phase(
        self,
        tools: list,
        target: str,
        scope: list[str],
        phase: str,
    ) -> list[dict]:
        """Ejecuta todas las tools de una fase en paralelo.

        Respeta el semáforo de concurrencia máxima.
        """
        tasks = [self._run_tool(tool, target, scope) for tool in tools]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings = []
        for tool, result in zip(tools, results):
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

    async def _run_tool(self, tool, target: str, scope: list[str]):
        async with self._semaphore:
            return await tool.safe_run(target, scope)

    def get_arsenal_status(self) -> dict:
        """Retorna estado de todas las herramientas registradas."""
        return ToolRegistry.all_tools_status()
