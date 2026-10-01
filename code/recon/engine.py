"""
ReconEngine — orquesta la ejecución de herramientas por fases.

Versión CLI: la aprobación de cada herramienta se solicita mediante un
callback (confirmación interactiva en terminal), sin base de datos.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from recon.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

DEFAULT_PHASES = [
    "subdomain_enum",
    "port_scan",
    "web_fingerprint",
    "crawl",
    "vuln_scan",
]

# Callback de aprobación: recibe (tool, target, scope, phase) y retorna
# True si el usuario aprueba ejecutar esa herramienta, False si la salta.
ApprovalCallback = Callable[["object", str, list[str], str], Awaitable[bool]]


class ReconEngine:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def run_scan(
        self,
        target: str,
        scope: list[str],
        phases: list[str] | None = None,
        approval_callback: ApprovalCallback | None = None,
    ) -> dict:
        """
        Ejecuta las fases de reconocimiento en orden.
        Retorna un dict con los findings agrupados por fase.

        approval_callback: función async que solicita aprobación humana
            antes de ejecutar cada herramienta. Si retorna False, la
            herramienta se salta. Si es None, se ejecutan todas.
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
                tools, target, scope, phase, approval_callback
            )
            all_findings[phase] = phase_findings

        return all_findings

    async def _run_phase(
        self,
        tools: list,
        target: str,
        scope: list[str],
        phase: str,
        approval_callback: ApprovalCallback | None = None,
    ) -> list[dict]:
        """Solicita aprobación de cada tool (secuencial) y ejecuta las
        aprobadas en paralelo respetando el semáforo de concurrencia.
        """
        if approval_callback:
            approved_tools = []
            for tool in tools:
                ok = await approval_callback(tool, target, scope, phase)
                if ok:
                    approved_tools.append(tool)
        else:
            approved_tools = tools

        if not approved_tools:
            return []

        tasks = [
            self._run_tool(tool, target, scope) for tool in approved_tools
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

    async def _run_tool(self, tool, target: str, scope: list[str]):
        async with self._semaphore:
            return await tool.safe_run(target, scope)

    def get_arsenal_status(self) -> dict:
        """Retorna estado de todas las herramientas registradas."""
        return ToolRegistry.all_tools_status()
