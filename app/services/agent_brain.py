import os
import json
import logging
import google.generativeai as genai
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AgentBrain:
    """
    El 'Cerebro' de SysMho Hunter. 
    Utiliza Gemini 1.5 Flash para razonar tácticamente sobre los hallazgos
    de Pentesting y proponer acciones al operador humano.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or "tu_api_key" in api_key:
            logger.error("GEMINI_API_KEY no configurada correctamente.")
            raise ValueError("API Key de Gemini faltante.")
        
        genai.configure(api_key=api_key)
        # Usamos Flash por su velocidad y ventana de contexto para logs extensos
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    async def reason_next_steps(self, target_url: str, recon_data: Dict[str, Any], previous_findings: List[Dict]) -> Dict[str, Any]:
        """
        Analiza los datos actuales y decide qué debería hacer el agente a continuación.
        """
        prompt = f"""
        Eres SysMho Hunter, un agente de IA experto en Pentesting Web y Bug Bounty para HackerOne.
        Tu objetivo es analizar los datos de reconocimiento y proponer el Siguiente Paso Lógico.

        OBJETIVO: {target_url}
        
        DATOS DE RECONOCIMIENTO (Puertos y Servicios):
        {json.dumps(recon_data.get('ports', []), indent=2)}
        
        DIRECTORIOS ENCONTRADOS:
        {json.dumps(recon_data.get('directories', []), indent=2)}
        
        HALLAZGOS PREVIOS:
        {json.dumps(previous_findings, indent=2)}

        INSTRUCCIONES:
        1. Evalúa la superficie de ataque.
        2. Identifica el vector de ataque más prometedor.
        3. Propón UNA acción inmediata (ej: Fuzzing específico, escaneo de vulnerabilidades X, búsqueda de exploits).
        4. Sé técnico y profesional.

        RESPONDE ÚNICAMENTE EN FORMATO JSON SIGUIENTE:
        {{
            "thought": "Tu razonamiento técnico sobre por qué este paso es importante",
            "action": "Nombre de la acción (fuzz_dir, vuln_scan, exploit_check, info_gathering)",
            "command_suggestion": "El comando o herramienta sugerida",
            "priority": "high/medium/low",
            "risk_level": "low/medium/high (impacto en el target)"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            # Limpiar respuesta para asegurar JSON válido
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error en razonamiento de IA: {e}")
            return {
                "thought": "Error al consultar al cerebro de IA. Procediendo con escaneo estándar.",
                "action": "standard_scan",
                "command_suggestion": "standard_tools",
                "priority": "medium",
                "risk_level": "low"
            }

    async def format_hackerone_report(self, target: str, finding: Dict) -> str:
        """
        Utiliza la IA para redactar un reporte profesional al estilo HackerOne.
        """
        prompt = f"""
        Redacta un reporte de Bug Bounty profesional para HackerOne basado en este hallazgo:
        OBJETIVO: {target}
        HALLAZGO: {finding}

        ESTRUCTURA REQUERIDA:
        - Summary
        - Impact
        - Steps to Reproduce
        - Remediation
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return "Falla al generar reporte automático."
