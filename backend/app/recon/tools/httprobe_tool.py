"""Wrapper para httprobe — detección de hosts HTTP/HTTPS activos."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class HttprobeTool(BaseTool):
    name = "httprobe"
    binary = "httprobe"
    phase = "web_fingerprint"
    risk_level = "low"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        # httprobe lee de stdin
        cmd = ["bash", "-c", f"echo {target} | {self.binary} -c 50"]
        stdout, stderr, exit_code = await self._execute(cmd)
        return ToolResult(
            tool_name=self.name,
            success=True,
            raw_output=stdout,
            stderr=stderr,
            exit_code=exit_code,
            parsed_findings=self.parse_output(stdout),
            command_executed=cmd[2],
        )

    def parse_output(self, raw_output: str) -> list[dict]:
        findings = []
        for line in raw_output.strip().splitlines():
            url = line.strip()
            if url.startswith("http"):
                findings.append(
                    {
                        "type": "web_service",
                        "title": f"Servicio web activo: {url}",
                        "severity": "informational",
                        "description": (
                            f"Host HTTP/HTTPS respondiendo en {url}"
                        ),
                        "url": url,
                    }
                )
        return findings
