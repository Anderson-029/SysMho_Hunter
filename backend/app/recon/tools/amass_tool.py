"""Wrapper para amass — descubrimiento de subdominios (más exhaustivo)."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class AmassTool(BaseTool):
    name = "amass"
    binary = "amass"
    phase = "subdomain_enum"
    risk_level = "low"
    default_timeout = 600

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        cmd = [
            self.binary,
            "enum",
            "-passive",
            "-d",
            target,
            "-o",
            "/dev/stdout",
        ]
        stdout, stderr, exit_code = await self._execute(
            cmd, timeout=self.default_timeout
        )
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
            if subdomain and "." in subdomain:
                findings.append(
                    {
                        "type": "subdomain",
                        "title": f"Subdominio: {subdomain}",
                        "severity": "informational",
                        "description": (
                            f"Subdominio descubierto por amass: {subdomain}"
                        ),
                        "url": subdomain,
                    }
                )
        return findings
