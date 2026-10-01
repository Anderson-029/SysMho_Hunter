# SysMho Hunter

> Agente autónomo de pentesting por línea de comandos. Reconocimiento
> asistido por un cerebro híbrido de IA (ML local → LLM local → cloud),
> con aprobación humana en cada paso y reportes conversacionales en terminal.

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![License](https://img.shields.io/badge/License-Authorized%20Use%20Only-red)

---

## ¿Qué es SysMho Hunter?

**SysMho Hunter** es una herramienta CLI para auditorías de seguridad web
autorizadas. Orquesta un arsenal de herramientas de reconocimiento, razona
sobre los hallazgos con un cerebro híbrido de 3 niveles y te entrega un
reporte en prosa, como lo haría un analista hablándote.

- Reconocimiento por fases (subdominios → puertos → fingerprint → crawl → vulns)
- **El agente propone cada herramienta y tú apruebas** antes de que toque el objetivo
- Cerebro híbrido: scikit-learn (ML) → Llama 3.1 8B (Ollama) → Gemini (cloud)
- Contexto técnico vía RAG (Qdrant + knowledge base propia)
- **Scope enforcement obligatorio**: los objetivos vienen de `scope.txt`, nunca hardcodeados
- Evidencia en archivos locales — sin base de datos, sin servidor

---

## Requisitos

### Sistema
- **Linux** (Debian/Ubuntu/Kali/Parrot/Arch probado)
- Python 3.12+
- [uv](https://astral.sh/uv) (gestor de dependencias)
- Algunas herramientas (nmap -sS, masscan) requieren `sudo`

### Opcional (cerebro completo)
- **Ollama** (`llama3.1:8b-instruct-q6_K`) — Nivel 2 del cerebro
- **Docker + Qdrant** — RAG (contexto técnico)
- **Modelos ML** (`ml/models/*.pkl`) — Nivel 1

> El sistema degrada con gracia: si falta Ollama, RAG o los modelos ML,
> el cerebro escala al siguiente nivel disponible y el pipeline sigue.

---

## Instalación

```bash
git clone <repo> SysMho_Hunter
cd SysMho_Hunter
uv sync                      # instala dependencias en .venv
cp .env.example .env         # rellena GEMINI_API_KEY si usarás cloud
```

Instalar el arsenal de herramientas de pentesting:
```bash
bash scripts/check_tools.sh            # ver qué falta
bash scripts/install_tools.sh          # instalar el arsenal
```

---

## Uso Rápido

### 1. Define tu scope autorizado

Crea `scope.txt` con los objetivos para los que **tienes permiso explícito**:
```
# dominios, *.wildcards, IPs o CIDRs
ejemplo-autorizado.com
*.ejemplo-autorizado.com
192.168.56.0/24
```

### 2. Modo interactivo (recomendado)

```bash
sudo python3 hunter.py -I
```
Te guía paso a paso: confirma autorización, elige objetivo, y el agente va
proponiendo cada herramienta mientras tú apruebas.

### 3. Modo directo (scripts / automatización)

```bash
# Pregunta antes de cada herramienta
sudo python3 hunter.py ejemplo-autorizado.com --scope scope.txt

# Auto-aprueba herramientas de riesgo bajo/medio
sudo python3 hunter.py ejemplo-autorizado.com --scope scope.txt --yes

# Solo fases específicas
sudo python3 hunter.py ejemplo-autorizado.com --phases subdomain_enum port_scan
```

---

## Evidencia Generada

Cada sesión produce:

```
output/
└── ejemplo-autorizado.com/
    └── 20260930_201122/
        ├── findings.json     ← todos los hallazgos estructurados
        ├── report.md         ← reporte conversacional en prosa
        ├── recon/            ← salida cruda por herramienta
        └── session.log       ← ciclo de vida (JSON: aprobaciones, decisiones)
```

---

## Arquitectura

| Módulo | Responsabilidad |
|--------|-----------------|
| `code/hunter.py` | Entry point: argparse, modos `-I` / directo |
| `code/cli/interactive.py` | Menú guiado del modo interactivo |
| `code/cli/render.py` | Salida conversacional + reporte markdown |
| `code/core/orchestrator.py` | Pipeline recon → cerebro → reporte, con aprobación |
| `code/core/scope.py` | Carga y validación de `scope.txt` + confirmación |
| `code/core/output.py` | Evidencia en archivos locales |
| `code/brain/` | Cerebro híbrido 3 niveles (ML → Ollama → cloud) + RAG |
| `code/recon/` | ReconEngine, BaseTool, 19 herramientas CLI |
| `code/rag/` | Qdrant + embeddings (contexto técnico) |
| `knowledge/` | Knowledge base indexada (RAG) |
| `ml/` | Modelos scikit-learn (Nivel 1) |

---

## Cerebro Híbrido

```
Nivel 1: ML (scikit-learn, <10ms)      → clasificación de severidad, scoring
   ↓ si confianza < umbral
Nivel 2: Ollama (Llama 3.1 8B, local)  → análisis, detección de patrones
   ↓ si confianza < umbral o no disponible
Nivel 3: Gemini (cloud, fallback)      → razonamiento complejo
```
Los niveles 2 y 3 reciben contexto adicional de RAG (best-effort).

---

## Aviso Legal

**SysMho Hunter está diseñado exclusivamente para auditorías de seguridad en
entornos controlados y con autorización explícita y por escrito.**

El uso no autorizado contra sistemas de terceros es **ilegal** y puede acarrear
consecuencias civiles y penales. El scope enforcement es una salvaguarda, no
un sustituto de tu responsabilidad: solo tú garantizas que tienes permiso.

Úsalo solo en tus propios sistemas, laboratorios, o con autorización
documentada del propietario del objetivo.

---

## Autor

**SysMho**
