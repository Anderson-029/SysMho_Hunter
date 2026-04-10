"""Wrapper para eyewitness — screenshots de interfaces web."""

import os

from app.recon.base_tool import BaseTool, ToolResult
from app.recon.tool_registry import ToolRegistry


@ToolRegistry.register
class EyewitnessTool(BaseTool):
    name = "eyewitness"
    binary = "eyewitness"
    phase = "web_fingerprint"
    risk_level = "low"
    default_timeout = 120

    def is_installed(self) -> bool:
        import shutil

        return (
            shutil.which("eyewitness") is not None
            or shutil.which("EyeWitness") is not None
        )

    async def run(self, target: str, scope: list[str], **kwargs) -> ToolResult:
        self._validate_scope(target, scope)
        output_dir = "/tmp/eyewitness_out"
        binary = (
            "eyewitness"
            if os.path.exists("/usr/bin/eyewitness")
            else "EyeWitness"
        )
        cmd = [binary, "--single", target, "-d", output_dir, "--no-prompt"]
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
        if (
            "screenshot" in raw_output.lower()
            or "captured" in raw_output.lower()
        ):
            findings.append(
                {
                    "type": "screenshot",
                    "title": "Screenshot capturado",
                    "severity": "informational",
                    "description": "Interfaz web capturada por eyewitness",
                    "url": "",
                }
            )
        return findings
