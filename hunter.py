#!/usr/bin/env python3
"""
SysMho Hunter — wrapper de arranque desde la raíz del proyecto.

Permite ejecutar el CLI sin entrar a code/:
    sudo python3 hunter.py -I
    sudo python3 hunter.py target.com --scope scope.txt

Internamente añade code/ al sys.path y delega en code/hunter.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "code"))

from hunter import main  # noqa: E402

if __name__ == "__main__":
    main()
