"""Wrapper para hakrawler — crawling de URLs y endpoints."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class HakrawlerTool(BaseTool):
    name = "hakrawler"
    binary = "hakrawler"
    phase = "crawl"
    risk_level = "low"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        depth = kwargs.get("depth", "2")
        cmd = [
            "bash",
            "-c",
            f"echo {target} | {self.binary} -depth {depth} -plain",
        ]
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
        seen = set()
        for line in raw_output.strip().splitlines():
            url = line.strip()
            if url.startswith("http") and url not in seen:
                seen.add(url)
                findings.append(
                    {
                        "type": "endpoint",
                        "title": f"Endpoint: {url}",
                        "severity": "informational",
                        "description": f"Endpoint descubierto: {url}",
                        "url": url,
                    }
                )
        return findings
