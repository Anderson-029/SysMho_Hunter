"""Wrapper para feroxbuster — fuzzing de directorios recursivo."""

import json

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class FeroxbusterTool(BaseTool):
    name = "feroxbuster"
    binary = "feroxbuster"
    phase = "vuln_scan"
    risk_level = "medium"
    default_timeout = 300

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        wordlist = kwargs.get(
            "wordlist", "/usr/share/wordlists/dirb/common.txt"
        )
        cmd = [
            self.binary,
            "--url",
            target,
            "--wordlist",
            wordlist,
            "--output",
            "/dev/stdout",
            "--json",
            "--silent",
            "--no-recursion",
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
        for line in raw_output.strip().splitlines():
            try:
                data = json.loads(line)
                if data.get("type") == "response" and data.get("status") in (
                    200,
                    201,
                    204,
                    301,
                    302,
                    403,
                ):
                    findings.append(
                        {
                            "type": "directory_found",
                            "title": f"Endpoint: {data.get('url', '')}",
                            "severity": "informational",
                            "description": (
                                f"Status: {data.get('status')},"
                                f" Tamaño: {data.get('content_length')}"
                                " bytes"
                            ),
                            "url": data.get("url", ""),
                        }
                    )
            except json.JSONDecodeError:
                continue
        return findings
