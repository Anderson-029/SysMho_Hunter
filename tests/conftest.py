"""
conftest.py — configuración de tests del CLI.

Añade code/ al sys.path para que los módulos (brain, recon, rag, core, ...)
sean importables sin instalar el paquete. Sin base de datos ni servidor.
"""

import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parent.parent / "code"
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
