"""Wrapper para ffuf — fuzzing de directorios y parámetros."""

import json

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class FfufTool(BaseTool):
    name = "ffuf"
    binary = "ffuf"
    phase = "vuln_scan"
    risk_level = "medium"
    default_timeout = 300

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        wordlist = kwargs.get(
            "wordlist", "/usr/share/wordlists/dirb/common.txt"
        )
        url = target if "FUZZ" in target else f"{target.rstrip('/')}/FUZZ"
        cmd = [
            self.binary,
            "-u",
            url,
            "-w",
            wordlist,
            "-of",
            "json",
            "-o",
            "/dev/stdout",
            "-s",
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
        try:
            data = json.loads(raw_output)
            for result in data.get("results", []):
                findings.append(
                    {
                        "type": "directory_found",
                        "title": (
                            "Directorio/endpoint: "
                            f"{result.get('input', {}).get('FUZZ', '')}"
                        ),
                        "severity": "informational",
                        "description": (
                            f"Status: {result.get('status')},"
                            f" Tamaño: {result.get('length')} bytes"
                        ),
                        "url": result.get("url", ""),
                    }
                )
        except json.JSONDecodeError:
            pass
        return findings
