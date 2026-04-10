"""Wrapper para gobuster — fuzzing de directorios y DNS."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class GobusterTool(BaseTool):
    name = "gobuster"
    binary = "gobuster"
    phase = "vuln_scan"
    risk_level = "medium"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        wordlist = kwargs.get(
            "wordlist", "/usr/share/wordlists/dirb/common.txt"
        )
        mode = kwargs.get("mode", "dir")
        cmd = [
            self.binary,
            mode,
            "-u",
            target,
            "-w",
            wordlist,
            "-q",
            "--no-error",
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
            line = line.strip()
            if (
                line
                and not line.startswith("Error")
                and not line.startswith("[")
            ):
                parts = line.split()
                url = parts[0] if parts else line
                status = ""
                for p in parts:
                    if p.startswith("(Status:"):
                        status = p
                findings.append(
                    {
                        "type": "directory_found",
                        "title": f"Recurso: {url}",
                        "severity": "informational",
                        "description": f"gobuster: {url} {status}",
                        "url": url,
                    }
                )
        return findings
