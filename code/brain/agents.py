"""
agents — agentes especializados del Nivel 2 del cerebro.

Cada agente combina un ROL (system prompt) con un MODELO de Ollama adecuado
para su tipo de tarea. El router resuelve qué agente atiende cada task_type
y le pasa su modelo + system prompt a LocalLLM.

Filosofía de recursos (equilibrio velocidad/capacidad):
- Trabajo frecuente → modelos 14b (rápidos, caben en memoria).
- Trabajo puntual (reporte final, payloads complejos) → modelos grandes.

Modelos configurables por env (ver config.py): AGENT_RECON_MODEL, etc.
Si un modelo no está instalado, LocalLLM degrada al modelo por defecto.
"""

from dataclasses import dataclass, field

from config import settings


@dataclass(frozen=True)
class Agent:
    name: str
    model: str
    system_prompt: str
    task_types: tuple[str, ...] = field(default_factory=tuple)


# Preámbulo común a todos los agentes (encuadre de uso autorizado).
_COMMON = (
    "You operate strictly within authorized security assessments. "
    "Be precise and technical. When asked for JSON, respond with valid "
    "JSON only, no prose outside it."
)

RECON_ANALYZER = Agent(
    name="ReconAnalyzer",
    model=settings.agent_recon_model,
    system_prompt=(
        "You are a reconnaissance analyst specialized in attack-surface "
        "mapping. Given recon data, identify the highest-impact, most "
        "promising next steps and explain your reasoning concisely. "
        f"{_COMMON}"
    ),
    task_types=("reason_next_steps",),
)

CODE_ANALYZER = Agent(
    name="CodeAnalyzer",
    model=settings.agent_code_model,
    system_prompt=(
        "You are a security analyst specialized in HTTP responses, code and "
        "configuration. You excel at spotting vulnerability patterns (XSS, "
        "SQLi, SSRF, IDOR, RCE, LFI, misconfigurations) and classifying them "
        f"accurately. {_COMMON}"
    ),
    task_types=("analyze_response", "detect_patterns"),
)

REPORT_WRITER = Agent(
    name="ReportWriter",
    model=settings.agent_report_model,
    system_prompt=(
        "You are a professional vulnerability report writer. Produce clear, "
        "well-structured, actionable reports with accurate severity and "
        "concrete remediation steps. Write in professional prose."
    ),
    task_types=("draft_report",),
)

# Activo: el orquestador ofrece 'craft_payload' tras el análisis (opt-in).
PAYLOAD_CRAFTER = Agent(
    name="PayloadCrafter",
    model=settings.agent_payload_model,
    system_prompt=(
        "You are a payload-crafting specialist for authorized penetration "
        "testing. Produce precise, non-destructive proof-of-concept payloads "
        "for the given vulnerability class, each with a short explanation of "
        "what it does and how to use it safely. Authorized testing only."
    ),
    task_types=("craft_payload",),
)

ALL_AGENTS: tuple[Agent, ...] = (
    RECON_ANALYZER,
    CODE_ANALYZER,
    REPORT_WRITER,
    PAYLOAD_CRAFTER,
)

# Índice task_type → Agent (construido una vez).
_BY_TASK: dict[str, Agent] = {
    task: agent for agent in ALL_AGENTS for task in agent.task_types
}


def resolve_agent(task_type: str) -> Agent | None:
    """Devuelve el agente que atiende un task_type, o None si ninguno."""
    return _BY_TASK.get(task_type)
