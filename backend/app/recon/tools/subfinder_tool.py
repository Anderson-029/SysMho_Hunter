"""Wrapper para subfinder — descubrimiento de subdominios."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class SubfinderTool(BaseTool):
    name = "subfinder"
    binary = "subfinder"
    phase = "subdomain_enum"
    risk_level = "low"
    default_timeout = 300

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        cmd = [self.binary, "-d", target, "-silent", "-o", "/dev/stdout"]
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
        for line in raw_output.strip().splitlines():
            subdomain = line.strip()
            if subdomain:
                findings.append(
                    {
                        "type": "subdomain",
                        "title": f"Subdominio encontrado: {subdomain}",
                        "severity": "informational",
                        "description": f"Subdominio activo: {subdomain}",
                        "url": subdomain,
                    }
                )
        return findings
