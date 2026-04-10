"""Wrapper para wfuzz — fuzzing de parámetros y paths."""

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class WfuzzTool(BaseTool):
    name = "wfuzz"
    binary = "wfuzz"
    phase = "vuln_scan"
    risk_level = "medium"

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        wordlist = kwargs.get(
            "wordlist", "/usr/share/wordlists/dirb/common.txt"
        )
        url = target if "FUZZ" in target else f"{target.rstrip('/')}/FUZZ"
        cmd = [self.binary, "-c", "-z", f"file,{wordlist}", "--hc", "404", url]
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
        for line in raw_output.splitlines():
            if "C=" in line and "L=" in line:
                parts = line.split()
                for p in parts:
                    if p.startswith("http"):
                        findings.append(
                            {
                                "type": "directory_found",
                                "title": f"Recurso encontrado: {p}",
                                "severity": "informational",
                                "description": f"wfuzz: {line.strip()}",
                                "url": p,
                            }
                        )
                        break
        return findings
