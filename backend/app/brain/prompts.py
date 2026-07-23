"""
Prompts centralizados para el cerebro híbrido.
build_reason_prompt() — razonamiento táctico de pentesting
build_report_prompt() — redacción de reporte HackerOne
"""


def rag_block(rag_context: str) -> str:
    """Bloque opcional de contexto RAG, vacío si no hay resultados."""
    if not rag_context:
        return ""
    return f"""

RELEVANT KNOWLEDGE BASE CONTEXT (OWASP/PortSwigger/past findings):
{rag_context}

Use this context to ground your reasoning in real techniques and \
terminology when relevant. Do not invent facts not supported by it."""


def build_reason_prompt(
    target_url: str,
    recon_data: dict,
    findings: list[dict],
    rag_context: str = "",
) -> str:
    ports = recon_data.get("ports", [])[:10]
    dirs = recon_data.get("directories", [])[:20]
    prev_findings = findings[:5]

    return f"""You are SysMho Hunter, an expert AI pentesting agent \
for HackerOne Bug Bounty.
Analyze the recon data and propose the next tactical step.

TARGET: {target_url}

OPEN PORTS/SERVICES (up to 10):
{ports}

DISCOVERED DIRECTORIES (up to 20):
{dirs}

PREVIOUS FINDINGS (up to 5):
{prev_findings}
{rag_block(rag_context)}

Respond ONLY with valid JSON matching this exact schema:
{{
  "thought": "Technical reasoning about the attack surface",
  "action": "fuzz_dir|vuln_scan|exploit_check|info_gathering|xss_test",
  "command_suggestion": "specific tool and flags to run",
  "priority": "high|medium|low",
  "risk_level": "low|medium|high"
}}"""


def build_report_prompt(
    target: str, finding: dict, rag_context: str = ""
) -> str:
    return f"""You are a professional Bug Bounty report writer \
for HackerOne.
Write a high-quality report based on this finding.

TARGET: {target}
FINDING:
- Title: {finding.get("title")}
- Type: {finding.get("vuln_type")}
- Severity: {finding.get("severity")}
- URL: {finding.get("url")}
- Description: {finding.get("description")}
- Proof of Concept: {finding.get("proof_of_concept", "N/A")}
- CVSS Score: {finding.get("cvss_score", "N/A")}
- CWE: {finding.get("cwe_id", "N/A")}
{rag_block(rag_context)}

Write the report in Markdown with these exact sections:
## Summary
## Impact
## Steps to Reproduce
## Remediation
## Supporting Material

Be specific, technical, and professional. Include CVSS vector if available."""
