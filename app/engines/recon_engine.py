"""
SysMho Hunter - Motor de Reconocimiento.

Ejecuta herramientas de descubrimiento como nmap y ffuf
para mapear la superficie de ataque del target.
"""

import asyncio
import json
import xml.etree.ElementTree as ET
import logging
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ReconEngine:
    """Motor de reconocimiento profesional usando subprocesos asíncronos."""

    def __init__(self, repository: Optional[Any] = None) -> None:
        """
        Inicializa el motor.
        
        Args:
            repository: Repositorio opcional para persistir logs de progreso.
        """
        self.repository = repository
        self.timeout = 300  # 5 minutos por herramienta

    async def _log(self, scan_id: Optional[int], level: str, message: str):
        """Helper para loguear progreso."""
        if self.repository and scan_id:
            await self.repository.add_log(scan_id, level, message)
        logger.info(f"[{level.upper()}] {message}")

    async def run_discovery(
        self,
        target: str,
        scan_id: Optional[int] = None
    ) -> dict[str, Any]:
        """
        Ejecuta el pipeline de reconocimiento.
        """
        parsed = urlparse(target)
        hostname = parsed.hostname or target
        
        await self._log(scan_id, "info", f"Iniciando reconocimiento para: {hostname}")

        # Ejecutar tareas en paralelo
        tasks = [
            self.scan_ports(hostname, scan_id),
            self.discover_directories(target, scan_id),
        ]
        
        results = await asyncio.gather(*tasks)
        
        combined_results = {
            "ports": results[0].get("ports", []),
            "services": results[0].get("services", []),
            "directories": results[1],
            "target": target,
            "hostname": hostname
        }
        
        await self._log(scan_id, "success", "Reconocimiento finalizado correctamente.")
        return combined_results

    async def scan_ports(self, hostname: str, scan_id: Optional[int] = None) -> dict[str, Any]:
        """Escaneo de puertos usando nmap de forma asíncrona."""
        await self._log(scan_id, "info", "Ejecutando nmap...")
        
        cmd = [
            "nmap", "-sV", "--top-ports", "100",
            "-oX", "-", hostname
        ]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            
            if proc.returncode != 0:
                await self._log(scan_id, "error", f"Nmap falló: {stderr.decode()}")
                return {"ports": [], "services": []}
                
            return self._parse_nmap_xml(stdout.decode())
            
        except asyncio.TimeoutError:
            await self._log(scan_id, "warning", "Timeout alcanzado en nmap.")
            return {"ports": [], "services": []}
        except Exception as e:
            await self._log(scan_id, "error", f"Error en nmap: {str(e)}")
            return {"ports": [], "services": []}

    def _parse_nmap_xml(self, xml_output: str) -> dict[str, Any]:
        """Parsea XML de nmap."""
        ports = []
        services = []
        try:
            root = ET.fromstring(xml_output)
            for port_elem in root.findall(".//port"):
                port_id = port_elem.get("portid")
                state = port_elem.find("state").get("state")
                if state == "open":
                    service = port_elem.find("service")
                    service_name = service.get("name") if service is not None else "unknown"
                    ports.append(int(port_id))
                    services.append({
                        "port": int(port_id),
                        "name": service_name,
                        "version": service.get("version", "") if service is not None else ""
                    })
        except Exception:
            pass
        return {"ports": ports, "services": services}

    async def discover_directories(self, target: str, scan_id: Optional[int] = None) -> list[dict]:
        """Fuzzing de directorios usando ffuf."""
        await self._log(scan_id, "info", "Ejecutando ffuf para descubrimiento de directorios...")
        
        # Wordlist por defecto (ajustar según disponibilidad)
        wordlist = "/usr/share/wordlists/dirb/common.txt"
        
        cmd = [
            "ffuf", "-u", f"{target.rstrip('/')}/FUZZ",
            "-w", wordlist,
            "-mc", "200,301,302",
            "-s", "-of", "json", "-o", "/dev/stdout"
        ]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            
            if stdout:
                data = json.loads(stdout.decode())
                results = []
                for res in data.get("results", []):
                    results.append({
                        "url": res.get("url"),
                        "status": res.get("status"),
                        "content_length": res.get("length")
                    })
                return results
        except Exception as e:
            await self._log(scan_id, "error", f"Error en ffuf: {str(e)}")
            
        return []
