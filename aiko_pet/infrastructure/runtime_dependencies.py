"""Check required offline libraries before constructing a desktop session."""

from __future__ import annotations

import math
import sys
from importlib import import_module
from importlib.metadata import version


class RuntimeDependencyError(RuntimeError):
    """An incomplete runtime must not become a failed in-game object action."""


def check_runtime_dependencies() -> None:
    try:
        engine = import_module("astronomy")
        instant = engine.Time.Make(2026, 1, 1, 12, 0, 0.0)
        values = (
            engine.SunPosition(instant).elon,
            engine.Ecliptic(engine.GeoMoon(instant)).elon,
            engine.MoonPhase(instant),
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Invalid Astronomy Engine result")
    except (ImportError, AttributeError, ValueError, TypeError) as error:
        raise RuntimeDependencyError(
            "Astronomy Engine fehlt oder funktioniert in dieser Python-Umgebung "
            "nicht.\n\n"
            f"Verwendetes Python: {sys.executable}\n\n"
            "Bitte Aiko_installieren.bat ausführen und anschließend "
            "Aiko_starten.bat verwenden. Beide nutzen die lokale .venv.\n"
            "Dein Spielstand wurde nicht geöffnet oder verändert."
        ) from error
    try:
        library = import_module("pyjokes")
        if version("pyjokes") != "0.8.3" or not library.get_jokes(
            language="de", category="neutral",
        ):
            raise ValueError("Unsupported pyjokes version or missing German content")
    except (ImportError, AttributeError, ValueError, TypeError) as error:
        raise RuntimeDependencyError(
            "Die benötigte Witzbibliothek pyjokes (Version 0.8.3) fehlt oder "
            "funktioniert in dieser Python-Umgebung nicht.\n\n"
            f"Verwendetes Python: {sys.executable}\n\n"
            "Bitte Aiko_installieren.bat ausführen und anschließend "
            "Aiko_starten.bat verwenden. Beide nutzen die lokale .venv.\n"
            "Dein Spielstand wurde nicht geöffnet oder verändert."
        ) from error
