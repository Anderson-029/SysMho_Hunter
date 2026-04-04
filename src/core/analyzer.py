"""
SysMho Hunter - Analizador de Vulnerabilidades con IA.

Utiliza un LLM (Gemini) para interpretar los datos de
reconocimiento y sugerir/verificar vulnerabilidades.
"""

import os
from typing import Any, Optional

from src.core.payloads import PayloadLibrary


class VulnAnalyzer:
    """Analizador de vulnerabilidades potenciado por IA."""

    def __init__(self) -> None:
        """Inicializa el analizador."""
        self.payloads = PayloadLibrary()
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    async def analyze(
        self,
        target: str,
        recon_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Analiza los datos de reconocimiento y busca vulnerabilidades.

        Args:
            target: URL objetivo.
            recon_data: Datos del reconocimiento previo.

        Returns:
            Lista de hallazgos con su severidad e impacto.
        """
        findings: list[dict[str, Any]] = []

        # Análisis de cabeceras de seguridad faltantes
        header_findings = self._check_security_headers(
            recon_data.get("headers", {})
        )
        findings.extend(header_findings)

        # Análisis de servicios expuestos
        service_findings = self._check_exposed_services(
            recon_data.get("services", [])
        )
        findings.extend(service_findings)

        # Análisis de directorios sensibles
        dir_findings = self._check_sensitive_directories(
            recon_data.get("directories", [])
        )
        findings.extend(dir_findings)

        # TODO: Integrar análisis con Gemini LLM para
        # correlación avanzada de hallazgos

        return findings

    def _check_security_headers(
        self, headers: dict[str, str]
    ) -> list[dict[str, Any]]:
        """
        Verifica la presencia de cabeceras de seguridad.

        Args:
            headers: Cabeceras HTTP del target.

        Returns:
            Lista de hallazgos por cabeceras faltantes.
        """
        findings: list[dict[str, Any]] = []
        required_headers = {
            "Strict-Transport-Security": {
                "severity": "medium",
                "description": (
                    "HSTS no configurado. El sitio es vulnerable "
                    "a ataques de downgrade SSL."
                ),
            },
            "X-Content-Type-Options": {
                "severity": "low",
                "description": (
                    "X-Content-Type-Options faltante. "
                    "Posible MIME-type sniffing."
                ),
            },
            "X-Frame-Options": {
                "severity": "medium",
                "description": (
                    "X-Frame-Options faltante. "
                    "Posible clickjacking."
                ),
            },
            "Content-Security-Policy": {
                "severity": "medium",
                "description": (
                    "CSP no configurado. "
                    "Mayor riesgo de XSS."
                ),
            },
            "X-XSS-Protection": {
                "severity": "low",
                "description": (
                    "X-XSS-Protection faltante. "
                    "Filtro XSS del navegador desactivado."
                ),
            },
        }

        for header, info in required_headers.items():
            if header not in headers:
                findings.append({
                    "type": "missing_header",
                    "title": f"Cabecera de seguridad faltante: {header}",
                    "severity": info["severity"],
                    "description": info["description"],
                    "remediation": (
                        f"Agregar la cabecera {header} "
                        f"en la configuración del servidor."
                    ),
                })

        return findings

    def _check_exposed_services(
        self, services: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Detecta servicios potencialmente peligrosos.

        Args:
            services: Lista de servicios descubiertos.

        Returns:
            Lista de hallazgos por servicios expuestos.
        """
        findings: list[dict[str, Any]] = []
        risky_services = {
            "ftp": "high",
            "telnet": "critical",
            "mysql": "high",
            "postgresql": "high",
            "redis": "critical",
            "mongodb": "critical",
            "memcached": "high",
        }

        for service in services:
            name = service.get("name", "").lower()
            if name in risky_services:
                findings.append({
                    "type": "exposed_service",
                    "title": (
                        f"Servicio sensible expuesto: "
                        f"{name} (puerto {service.get('port')})"
                    ),
                    "severity": risky_services[name],
                    "description": (
                        f"El servicio {name} está expuesto "
                        f"públicamente en el puerto "
                        f"{service.get('port')}. "
                        f"Versión: {service.get('version', 'N/A')}."
                    ),
                    "remediation": (
                        f"Restringir acceso a {name} mediante "
                        f"firewall o VPN."
                    ),
                })

        return findings

    def _check_sensitive_directories(
        self, directories: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Detecta directorios y archivos sensibles.

        Args:
            directories: Lista de directorios descubiertos.

        Returns:
            Lista de hallazgos por recursos sensibles.
        """
        findings: list[dict[str, Any]] = []
        sensitive_patterns = [
            ".git", ".env", ".htaccess", "wp-admin",
            "admin", "backup", "config", "phpinfo",
            ".svn", "debug", "test", "api/swagger",
            "graphql", ".well-known",
        ]

        for directory in directories:
            url = directory.get("url", "").lower()
            status = directory.get("status", 0)

            for pattern in sensitive_patterns:
                if pattern in url and status in (200, 301, 302, 403):
                    severity = "high" if pattern in (
                        ".git", ".env", "backup", "config"
                    ) else "medium"
                    findings.append({
                        "type": "sensitive_directory",
                        "title": (
                            f"Recurso sensible descubierto: "
                            f"{directory.get('url')}"
                        ),
                        "severity": severity,
                        "description": (
                            f"El recurso '{pattern}' fue encontrado "
                            f"con código de estado {status}."
                        ),
                        "remediation": (
                            f"Restringir acceso al recurso o "
                            f"eliminarlo del servidor público."
                        ),
                    })
                    break

        return findings
