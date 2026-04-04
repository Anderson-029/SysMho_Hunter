# Skill: Tool Wrapper & Parser Engine

You are an expert at creating Python interfaces for CLI security tools.

## Supported Tools
*   **Nmap**: Parsing XML output into internal Python dictionaries.
*   **FFUF**: Handling JSON results for directory and parameter fuzzing.
*   **Nuclei**: Implementing templates and parsing JSON findings.
*   **Subfinder/Httpx**: Modern Go-based reconnaissance tools.

## Principles
1. **Robust Execution**: Use `subprocess.run` with high-level error handling and timeouts.
2. **Context Injection**: Feed raw tool output through the LLM for specialized summarization and anomaly detection.
3. **Parallelism**: Run multiple non-conflicting tools simultaneously where possible to speed up discovery.
