"""Wrapper para nuclei — escaneo de vulnerabilidades con templates."""

import json

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry

SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "informational",
}


@ToolRegistry.register
class NucleiTool(BaseTool):
    name = "nuclei"
    binary = "nuclei"
    phase = "vuln_scan"
    risk_level = "medium"
    default_timeout = 600

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        severity = kwargs.get("severity", "critical,high,medium")
        cmd = [
            self.binary,
            "-u",
            target,
            "-severity",
            severity,
            "-jsonl",
            "-silent",
            "-no-color",
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
            try:
                data = json.loads(line)
                findings.append(
                    {
                        "type": data.get("type", "nuclei_finding"),
                        "title": data.get("info", {}).get(
                            "name", "Nuclei finding"
                        ),
                        "severity": SEVERITY_MAP.get(
                            data.get("info", {}).get("severity", "info"),
                            "informational",
                        ),
                        "description": data.get("info", {}).get(
                            "description", ""
                        ),
                        "url": data.get("matched-at", data.get("host", "")),
                        "remediation": data.get("info", {}).get(
                            "remediation", ""
                        ),
                        "cwe_id": (
                            data.get("info", {})
                            .get("classification", {})
                            .get("cwe-id")
                            or [None]
                        )[0],
                        "cvss_score": data.get("info", {})
                        .get("classification", {})
                        .get("cvss-score"),
                    }
                )
            except json.JSONDecodeError:
                continue
        return findings
