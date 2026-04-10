"""Wrapper para masscan — escaneo de puertos a alta velocidad."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class MasscanTool(BaseTool):
    name = "masscan"
    binary = "masscan"
    phase = "port_scan"
    risk_level = "medium"
    default_timeout = 300

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        ports = kwargs.get("ports", "1-1024")
        rate = kwargs.get("rate", "1000")
        cmd = [
            "sudo",
            self.binary,
            target,
            "-p",
            ports,
            "--rate",
            rate,
            "--open-only",
            "-oL",
            "-",
        ]
        stdout, stderr, exit_code = await self._execute(cmd)
        return ToolResult(
            tool_name=self.name,
            success=(exit_code == 0),
            raw_output=stdout,
            stderr=stderr,
            exit_code=exit_code,
            parsed_findings=self.parse_output(stdout),
            command_executed=" ".join(cmd),
        )

    def parse_output(self, raw_output: str) -> list[dict]:
        findings = []
        for line in raw_output.splitlines():
            if line.startswith("open"):
                parts = line.split()
                if len(parts) >= 4:
                    proto, port, ip = parts[1], parts[2], parts[3]
                    findings.append(
                        {
                            "type": "open_port",
                            "title": f"Puerto {port}/{proto} abierto en {ip}",
                            "severity": "informational",
                            "description": (
                                f"masscan detectó {proto} {port}"
                                f" abierto en {ip}"
                            ),
                            "url": ip,
                        }
                    )
        return findings
