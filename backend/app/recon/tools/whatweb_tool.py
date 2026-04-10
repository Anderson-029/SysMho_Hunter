"""Wrapper para whatweb — fingerprinting de tecnologías web."""

import json

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class WhatwebTool(BaseTool):
    name = "whatweb"
    binary = "whatweb"
    phase = "web_fingerprint"
    risk_level = "low"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        cmd = [self.binary, "--log-json=-", target]
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
        try:
            for line in raw_output.strip().splitlines():
                data = json.loads(line)
                url = data.get("target", "")
                plugins = data.get("plugins", {})
                techs = list(plugins.keys())
                if techs:
                    findings.append(
                        {
                            "type": "technology_detected",
                            "title": f"Tecnologías detectadas en {url}",
                            "severity": "informational",
                            "description": f"Tecnologías: {', '.join(techs)}",
                            "url": url,
                        }
                    )
        except Exception:
            pass
        return findings
