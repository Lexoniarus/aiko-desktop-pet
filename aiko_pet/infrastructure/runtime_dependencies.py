"""Check required offline libraries before constructing a desktop session."""

from __future__ import annotations

import math
import sys
from importlib import import_module

from ..application.runtime_resources import PreparedRuntimeResources
from .local_jokes import LocalJokeCatalogError, load_local_jokes


class RuntimeDependencyError(RuntimeError):
    """An incomplete runtime must not become a failed in-game object action."""


def _check_astronomy() -> None:
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


def prepare_runtime_resources() -> PreparedRuntimeResources:
    """Validate once and return the exact resources for desktop composition."""
    _check_astronomy()
    try:
        return PreparedRuntimeResources(load_local_jokes())
    except LocalJokeCatalogError as error:
        explanation, repair = {
            "dependency": (
                "Die benötigte Witzbibliothek pyjokes (Version 0.8.3) fehlt oder "
                "hat eine andere Version.",
                "Bitte Aiko_installieren.bat ausführen und anschließend "
                "Aiko_starten.bat verwenden. Beide nutzen die lokale .venv.",
            ),
            "review": (
                "Die Freigabeliste der lokalen Witze fehlt oder ist beschädigt.",
                "Bitte die vollständigen Aiko-Projektdateien in einen frischen "
                "Ordner entpacken und dort Aiko_installieren.bat ausführen.",
            ),
            "content": (
                "Die lokalen Witztexte stimmen nicht mit der geprüften "
                "Freigabeliste überein oder sind unvollständig.",
                "Bitte Aiko in einen frischen Ordner entpacken und dort "
                "Aiko_installieren.bat ausführen, damit auch die .venv neu entsteht.",
            ),
        }[error.kind]
        raise RuntimeDependencyError(
            f"{explanation}\n\n"
            f"Verwendetes Python: {sys.executable}\n\n"
            f"{repair}\n"
            "Dein Spielstand wurde nicht geöffnet oder verändert."
        ) from error


def check_runtime_dependencies() -> None:
    """Compatibility check for setup and existing callers needing no resources."""
    prepare_runtime_resources()
