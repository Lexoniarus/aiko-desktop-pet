"""Canonical source checkout entry point for Aiko Desktop Pet.

Run with `python main.py` to choose the desktop or local room version.
"""

import subprocess
import sys
from pathlib import Path

from aiko_pet.desktop.version_launcher import choose_desktop


def desktop_checkout(checkout: Path) -> Path | None:
    try:
        desktop = checkout.with_name("aiko-desktop-pet").resolve()
    except (OSError, RuntimeError):
        return None
    package = desktop / "aiko_pet"
    if (
        desktop == checkout
        or not (package / "__main__.py").is_file()
        or not (package / "gui.py").is_file()
        or (package / "browser" / "bootstrap.py").is_file()
    ):
        return None
    return desktop


def main() -> None:
    checkout = Path(__file__).resolve().parent
    companion = checkout.with_name("aiko-desktop-pet")
    desktop = desktop_checkout(checkout)
    starter = checkout / "dist" / "room" / "starter"
    if not starter.is_dir() and companion != checkout:
        companion_starter = companion / "dist" / "room" / "starter"
        if companion_starter.is_dir():
            starter = companion_starter
    desktop_error = None
    if desktop is None:
        desktop_error = (
            f"Der Desktop-Checkout fehlt oder ist keine Desktop-Version.\n\n{companion}"
        )
    if not choose_desktop(starter, desktop_error=desktop_error) or desktop is None:
        return
    interpreter = desktop / ".venv" / "Scripts" / "python.exe"
    result = subprocess.run(
        [
            str(interpreter) if interpreter.is_file() else sys.executable,
            "-E",
            "-m",
            "aiko_pet",
        ],
        cwd=desktop,
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
