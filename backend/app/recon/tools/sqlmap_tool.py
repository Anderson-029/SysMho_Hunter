"""
Wrapper para sqlmap — detección de SQL injection.
RIESGO CRÍTICO: crea pending_action antes de ejecutar en modo agresivo.
Modo por defecto: --level=1 --risk=1 (no destructivo).
"""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class SqlmapTool(BaseTool):
    name = "sqlmap"
    binary = "sqlmap"
    phase = "vuln_scan"
    risk_level = "medium"  # medium en modo básico, critical en modo agresivo
    default_timeout = 300

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        level = kwargs.get("level", 1)
        risk = kwargs.get("risk", 1)
        # Nunca superar level=3/risk=2 sin aprobación humana
        level = min(int(level), 3)
        risk = min(int(risk), 2)
        cmd = [
            self.binary,
            "-u",
            target,
            "--level",
            str(level),
            "--risk",
            str(risk),
            "--batch",
            "--output-dir",
            "/tmp/sqlmap_out",
            "--forms",
            "--crawl=1",
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
        vulnerable_params = []
        for line in raw_output.splitlines():
            if "is vulnerable" in line.lower() or "parameter:" in line.lower():
                vulnerable_params.append(line.strip())
            if "sql injection" in line.lower() and "found" in line.lower():
                findings.append(
                    {
                        "type": "sqli",
                        "title": "SQL Injection detectado",
                        "severity": "critical",
                        "description": "\n".join(vulnerable_params)
                        or line.strip(),
                        "url": "",
                        "cwe_id": "CWE-89",
                    }
                )
        return findings
