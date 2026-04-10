"""Wrapper para dalfox — detección de XSS."""

import json

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class DalfoxTool(BaseTool):
    name = "dalfox"
    binary = "dalfox"
    phase = "vuln_scan"
    risk_level = "medium"
    default_timeout = 300

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        cmd = [self.binary, "url", target, "--format", "json", "--silence"]
        stdout, stderr, exit_code = await self._execute(cmd)
        return ToolResult(
            tool_name=self.name,
            success=(exit_code == 0),
            raw_output=stdout,
            stderr=stderr,
            exit_code=exit_code,
            parsed_findings=self.parse_output(stdout, target_url=target),
            command_executed=" ".join(cmd),
        )

    def parse_output(
        self, raw_output: str, target_url: str = ""
    ) -> list[dict]:
        """Parsea salida de dalfox en formato JSON o texto plano."""
        findings = []
        for line in raw_output.strip().splitlines():
            try:
                data = json.loads(line)
                if data.get("type") == "G":  # G = Good (vulnerability found)
                    findings.append(
                        {
                            "type": "xss",
                            "title": (
                                "XSS Reflejado detectado en "
                                f"{data.get('data', {}).get('url', '')}"
                            ),
                            "severity": "high",
                            "description": (
                                "Payload XSS: "
                                + str(
                                    data.get("data", {}).get(
                                        "injectedParam", ""
                                    )
                                )
                            ),
                            "url": data.get("data", {}).get("url", ""),
                            "cwe_id": "CWE-79",
                        }
                    )
            except json.JSONDecodeError:
                if "[V]" in line or "[POC]" in line:
                    findings.append(
                        {
                            "type": "xss",
                            "title": "XSS detectado por dalfox",
                            "severity": "high",
                            "description": line.strip(),
                            "url": target_url,
                            "cwe_id": "CWE-79",
                        }
                    )
        return findings
