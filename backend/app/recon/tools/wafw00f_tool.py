"""Wrapper para wafw00f — detección de Web Application Firewalls."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class Wafw00fTool(BaseTool):
    name = "wafw00f"
    binary = "wafw00f"
    phase = "web_fingerprint"
    risk_level = "low"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        cmd = [self.binary, target, "-o", "-", "-f", "json"]
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
        import json

        findings = []
        try:
            data = json.loads(raw_output)
            for entry in data:
                waf = entry.get("firewall", "")
                url = entry.get("url", "")
                if waf and waf.lower() not in ("none", ""):
                    findings.append(
                        {
                            "type": "waf_detected",
                            "title": f"WAF detectado: {waf}",
                            "severity": "informational",
                            "description": (
                                f"Web Application Firewall '{waf}'"
                                f" detectado en {url}"
                            ),
                            "url": url,
                        }
                    )
        except Exception:
            # Parseo de texto plano como fallback
            for line in raw_output.splitlines():
                if "is behind" in line.lower():
                    findings.append(
                        {
                            "type": "waf_detected",
                            "title": line.strip(),
                            "severity": "informational",
                            "description": line.strip(),
                            "url": "",
                        }
                    )
        return findings
