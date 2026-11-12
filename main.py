"""Canonical source checkout entry point for Aiko Desktop Pet.

Run with `python main.py` to choose the desktop or local room version.
"""

import subprocess
import sys
from pathlib import Path

from aiko_pet.desktop.version_launcher import choose_desktop


def main() -> None:
    checkout = Path(__file__).resolve().parent
    desktop = checkout.with_name("aiko-desktop-pet")
    starter = checkout / "dist" / "room" / "starter"
    if not starter.is_dir() and desktop != checkout:
        companion_starter = desktop / "dist" / "room" / "starter"
        if companion_starter.is_dir():
            starter = companion_starter
    if not choose_desktop(starter):
        return
    # The companion desktop build owns the native save schema.
    if desktop != checkout and (desktop / "aiko_pet" / "__main__.py").is_file():
        interpreter = desktop / ".venv" / "Scripts" / "python.exe"
        result = subprocess.run(
            [
                str(interpreter) if interpreter.is_file() else sys.executable,
                "-m",
                "aiko_pet",
            ],
            cwd=desktop,
            check=False,
        )
        if result.returncode:
            raise SystemExit(result.returncode)
    else:
        from aiko_pet.gui import main as start_desktop

        start_desktop()


if __name__ == "__main__":
    main()
