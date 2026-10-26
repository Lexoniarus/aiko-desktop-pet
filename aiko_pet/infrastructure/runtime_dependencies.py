"""Check required offline libraries before constructing a desktop session."""

from __future__ import annotations

import math
import sys
from importlib import import_module


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
