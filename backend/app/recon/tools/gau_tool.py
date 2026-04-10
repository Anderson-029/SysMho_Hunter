"""Wrapper para gau — URLs históricas (wayback, commoncrawl, etc.)."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class GauTool(BaseTool):
    name = "gau"
    binary = "gau"
    phase = "crawl"
    risk_level = "low"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        cmd = [self.binary, "--threads", "5", "--o", "/dev/stdout", target]
        stdout, stderr, exit_code = await self._execute(cmd)
        return ToolResult(
            tool_name=self.name,
            success=True,
            raw_output=stdout,
            stderr=stderr,
            exit_code=exit_code,
            parsed_findings=self.parse_output(stdout),
            command_executed=" ".join(cmd),
        )

    def parse_output(self, raw_output: str) -> list[dict]:
        findings = []
        seen = set()
        for line in raw_output.strip().splitlines():
            url = line.strip()
            if url.startswith("http") and url not in seen:
                seen.add(url)
                findings.append(
                    {
                        "type": "historical_url",
                        "title": f"URL histórica: {url[:100]}",
                        "severity": "informational",
                        "description": (
                            f"URL encontrada en archivos históricos: {url}"
                        ),
                        "url": url,
                    }
                )
        return findings
