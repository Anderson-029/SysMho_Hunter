"""Wrapper para nikto — escáner de vulnerabilidades web."""

import json

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class NiktoTool(BaseTool):
    name = "nikto"
    binary = "nikto"
    phase = "vuln_scan"
    risk_level = "medium"
    default_timeout = 300

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        cmd = [
            self.binary,
            "-h",
            target,
            "-Format",
            "json",
            "-o",
            "/dev/stdout",
            "-nointeractive",
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
            for vuln in data.get("vulnerabilities", []):
                findings.append(
                    {
                        "type": "web_vulnerability",
                        "title": vuln.get("msg", "Nikto finding")[:200],
                        "severity": "medium",
                        "description": vuln.get("msg", ""),
                        "url": vuln.get("url", ""),
                    }
                )
        except json.JSONDecodeError:
            # Parseo de texto plano como fallback
            for line in raw_output.splitlines():
                if line.startswith("+ ") and "OSVDB" not in line:
                    findings.append(
                        {
                            "type": "web_vulnerability",
                            "title": line[2:100],
                            "severity": "medium",
                            "description": line[2:],
                            "url": "",
                        }
                    )
        return findings
