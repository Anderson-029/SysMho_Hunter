"""Wrapper para nmap — escaneo de puertos y servicios."""

import xml.etree.ElementTree as ET

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class NmapTool(BaseTool):
    name = "nmap"
    binary = "nmap"
    phase = "port_scan"
    risk_level = "medium"
    default_timeout = 600

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        ports = kwargs.get("ports", "1-65535")
        cmd = [
            self.binary,
            "-sV",
            "-sC",
            "-T4",
            "--open",
            "-oX",
            "-",
            "-p",
            ports,
            target,
        ]
        stdout, stderr, exit_code = await self._execute(
            cmd, timeout=self.default_timeout
        )
        findings = self.parse_output(stdout)
        return ToolResult(
            tool_name=self.name,
            success=(exit_code == 0),
            raw_output=stdout,
            stderr=stderr,
            exit_code=exit_code,
            parsed_findings=findings,
            command_executed=" ".join(cmd),
        )

    def parse_output(self, raw_output: str) -> list[dict]:
        findings = []
        try:
            root = ET.fromstring(raw_output)
            for host in root.findall("host"):
                addr_el = host.find("address[@addrtype='ipv4']")
                addr = addr_el.get("addr", "") if addr_el is not None else ""
                for port_el in host.findall(".//port"):
                    state_el = port_el.find("state")
                    if state_el is None or state_el.get("state") != "open":
                        continue
                    service_el = port_el.find("service")
                    svc = service_el if service_el is not None else None
                    svc_name = svc.get("name", "unknown") if svc else "unknown"
                    svc_ver = svc.get("version", "") if svc else ""
                    port_id = port_el.get("portid")
                    proto = port_el.get("protocol")
                    findings.append(
                        {
                            "type": "open_port",
                            "title": (
                                f"Puerto {port_id}/{proto} abierto"
                            ),
                            "severity": "informational",
                            "description": (
                                f"Host: {addr}, Servicio: {svc_name},"
                                f" Versión: {svc_ver}"
                            ),
                            "url": addr,
                        }
                    )
        except ET.ParseError:
            pass
        return findings
