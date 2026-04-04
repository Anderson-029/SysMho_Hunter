"""
SysMho Hunter - Motor de Reconocimiento.

Ejecuta herramientas de descubrimiento como nmap y ffuf
para mapear la superficie de ataque del target.
"""

import asyncio
import json
import subprocess
import xml.etree.ElementTree as ET
from typing import Any, Optional
from urllib.parse import urlparse


class ReconEngine:
    """Motor de reconocimiento pasivo y activo."""

    def __init__(self) -> None:
        """Inicializa el motor de reconocimiento."""
        self.timeout = 120  # Timeout en segundos por herramienta

    async def run(
        self,
        target: str,
        scope: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Ejecuta el pipeline de reconocimiento completo.

        Args:
            target: URL o dominio objetivo.
            scope: Lista opcional de dominios permitidos.

        Returns:
            Diccionario con datos recopilados.
        """
        parsed = urlparse(target)
        hostname = parsed.hostname or target
        results: dict[str, Any] = {
            "target": target,
            "hostname": hostname,
            "ports": [],
            "services": [],
            "directories": [],
            "technologies": [],
            "headers": {},
        }

        # Ejecutar reconocimiento en paralelo
        tasks = [
            self._scan_ports(hostname),
            self._discover_directories(target),
            self._analyze_headers(target),
        ]
        port_data, dir_data, header_data = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        if isinstance(port_data, dict):
            results["ports"] = port_data.get("ports", [])
            results["services"] = port_data.get("services", [])

        if isinstance(dir_data, list):
            results["directories"] = dir_data

        if isinstance(header_data, dict):
            results["headers"] = header_data
            results["technologies"] = self._detect_tech(header_data)

        return results

    async def _scan_ports(self, hostname: str) -> dict[str, Any]:
        """
        Escanea los puertos más comunes con nmap.

        Args:
            hostname: Host objetivo para el escaneo.

        Returns:
            Diccionario con puertos y servicios encontrados.
        """
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "nmap", "-sV", "--top-ports", "100",
                    "-oX", "-", hostname,
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode != 0:
                return {"ports": [], "services": []}

            return self._parse_nmap_xml(result.stdout)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"ports": [], "services": []}

    def _parse_nmap_xml(self, xml_output: str) -> dict[str, Any]:
        """
        Parsea el output XML de nmap.

        Args:
            xml_output: Cadena XML de la salida de nmap.

        Returns:
            Diccionario con puertos y servicios estructurados.
        """
        ports = []
        services = []

        try:
            root = ET.fromstring(xml_output)
            for host in root.findall(".//host"):
                for port_elem in host.findall(".//port"):
                    port_id = port_elem.get("portid", "")
                    protocol = port_elem.get("protocol", "")
                    state_elem = port_elem.find("state")
                    service_elem = port_elem.find("service")

                    state = (
                        state_elem.get("state", "unknown")
                        if state_elem is not None
                        else "unknown"
                    )

                    if state == "open":
                        port_info = {
                            "port": int(port_id),
                            "protocol": protocol,
                            "state": state,
                        }

                        if service_elem is not None:
                            service_name = service_elem.get("name", "")
                            service_version = service_elem.get(
                                "version", ""
                            )
                            port_info["service"] = service_name
                            port_info["version"] = service_version
                            services.append({
                                "name": service_name,
                                "version": service_version,
                                "port": int(port_id),
                            })

                        ports.append(port_info)
        except ET.ParseError:
            pass

        return {"ports": ports, "services": services}

    async def _discover_directories(
        self, target: str
    ) -> list[dict[str, Any]]:
        """
        Descubre directorios y archivos con ffuf.

        Args:
            target: URL objetivo para fuzzing de directorios.

        Returns:
            Lista de directorios encontrados.
        """
        wordlist = "/usr/share/wordlists/dirb/common.txt"
        directories: list[dict[str, Any]] = []

        try:
            fuzz_url = f"{target.rstrip('/')}/FUZZ"
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "ffuf", "-u", fuzz_url,
                    "-w", wordlist,
                    "-mc", "200,301,302,403",
                    "-t", "10",  # Hilos limitados (rate limiting)
                    "-o", "/dev/stdout",
                    "-of", "json",
                    "-s",  # Modo silencioso
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.stdout:
                data = json.loads(result.stdout)
                for entry in data.get("results", []):
                    directories.append({
                        "url": entry.get("url", ""),
                        "status": entry.get("status", 0),
                        "length": entry.get("length", 0),
                        "words": entry.get("words", 0),
                    })

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            json.JSONDecodeError,
        ):
            pass

        return directories

    async def _analyze_headers(self, target: str) -> dict[str, str]:
        """
        Analiza las cabeceras HTTP del target.

        Args:
            target: URL objetivo.

        Returns:
            Diccionario con las cabeceras de respuesta.
        """
        import aiohttp

        headers: dict[str, str] = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(
                    target, timeout=aiohttp.ClientTimeout(total=15),
                    allow_redirects=True,
                    ssl=False,
                ) as response:
                    headers = dict(response.headers)
        except Exception:
            pass

        return headers

    def _detect_tech(
        self, headers: dict[str, str]
    ) -> list[str]:
        """
        Detecta tecnologías basándose en cabeceras HTTP.

        Args:
            headers: Cabeceras HTTP de la respuesta.

        Returns:
            Lista de tecnologías detectadas.
        """
        tech_signatures: dict[str, str] = {
            "X-Powered-By": "framework",
            "Server": "server",
            "X-AspNet-Version": "ASP.NET",
            "X-Drupal-Cache": "Drupal",
            "X-Generator": "generator",
        }

        detected: list[str] = []
        for header, label in tech_signatures.items():
            value = headers.get(header)
            if value:
                detected.append(f"{label}: {value}")

        return detected
