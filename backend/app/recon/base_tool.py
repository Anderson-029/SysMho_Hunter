"""
BaseTool — clase abstracta para todos los wrappers de herramientas CLI.
"""

import asyncio
import fnmatch
import ipaddress
import shutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from urllib.parse import urlparse


class ScopeViolationError(Exception):
    def __init__(self, target: str):
        super().__init__(
            f"Target '{target}' fuera de scope — operación bloqueada."
        )


class ToolNotInstalledError(Exception):
    def __init__(self, tool_name: str):
        super().__init__(
            f"Herramienta '{tool_name}' no instalada en el sistema."
        )


class ToolTimeoutError(Exception):
    def __init__(self, tool_name: str, timeout: int):
        super().__init__(
            f"Herramienta '{tool_name}' excedió el timeout de {timeout}s."
        )


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    raw_output: str
    stderr: str
    exit_code: int
    parsed_findings: list[dict] = field(default_factory=list)
    execution_time_ms: int = 0
    command_executed: str = ""


class BaseTool(ABC):
    name: str = ""
    binary: str = ""
    phase: str = ""
    risk_level: str = "low"  # low|medium|high|critical
    default_timeout: int = 300

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._available: bool | None = None

    def is_installed(self) -> bool:
        if self._available is None:
            self._available = shutil.which(self.binary) is not None
        return self._available

    def _validate_scope(self, target: str, scope: list[str]) -> bool:
        """
        CRÍTICO: verifica que target esté dentro del scope antes de ejecutar.
        scope es una lista de valores (dominios, IPs, CIDRs, wildcards).
        Retorna True si está en scope, lanza ScopeViolationError si no.
        """
        # Extraer hostname/IP del target (puede ser URL)
        parsed = urlparse(target)
        host = parsed.hostname or target

        for s in scope:
            # Wildcard de dominio: *.example.com
            if s.startswith("*."):
                domain = s[2:]
                if host == domain or host.endswith("." + domain):
                    return True
            # Coincidencia exacta de dominio
            elif fnmatch.fnmatch(host, s):
                return True
            # CIDR o IP
            else:
                try:
                    network = ipaddress.ip_network(s, strict=False)
                    ip = ipaddress.ip_address(host)
                    if ip in network:
                        return True
                except ValueError:
                    continue

        raise ScopeViolationError(target)

    async def _execute(
        self,
        cmd: list[str],
        timeout: int | None = None,
        env: dict | None = None,
    ) -> tuple[str, str, int]:
        """Ejecuta un comando async con timeout.

        Retorna (stdout, stderr, exit_code).
        """
        timeout = timeout or self.default_timeout
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise ToolTimeoutError(self.name, timeout)
        return (
            stdout_b.decode(errors="replace"),
            stderr_b.decode(errors="replace"),
            proc.returncode or 0,
        )

    @abstractmethod
    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        """Ejecutar la herramienta contra target.

        Siempre validar scope antes de ejecutar.
        """
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> list[dict]:
        """Convertir salida cruda en lista de findings estructurados."""
        ...

    async def safe_run(
        self, target: str, scope: list[str], **kwargs
    ) -> ToolResult:
        """Wrapper que valida instalación y scope antes de ejecutar."""
        if not self.is_installed():
            raise ToolNotInstalledError(self.name)
        self._validate_scope(target, scope)
        start = time.monotonic()
        result = await self.run(target, scope, **kwargs)
        result.execution_time_ms = int((time.monotonic() - start) * 1000)
        return result
