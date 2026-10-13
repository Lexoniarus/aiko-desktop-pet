"""Architectural completion gates for canonical modules and projections."""

from __future__ import annotations

import ast
import random
import unittest
from datetime import datetime
from pathlib import Path


from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.application.settings import PetSettings
from aiko_pet.personality.mind import AikoMind
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState

from aiko_pet.presentation.projections import (
    project_hover, project_settings, project_status,
)
from aiko_pet.telemetry import ComputerSnapshot


ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"


class FinalArchitectureTests(unittest.TestCase):
    def test_active_application_has_no_outer_layer_imports(self) -> None:
        forbidden = (
            "presentation", "ui", "desktop",
            "infrastructure", "storage", "system_activity",
        )
        for path in (ROOT / "application").glob("*.py"):
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text("utf-8"))
                imports = [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ] + [
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                ]
                for name in imports:
                    suffix = (
                        name.removeprefix("aiko_pet.")
                        if name.startswith("aiko_pet.") else name
                    )
                    self.assertFalse(
                        suffix.startswith(forbidden),
                        f"{path.name} imports outer layer {name}",
                    )

    def test_presentation_has_no_tk_provider_or_legacy_monitor_import(self) -> None:
        for path in (ROOT / "presentation").glob("*.py"):
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text("utf-8"))
                imports = [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ] + [
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                ]
                for name in imports:
                    self.assertFalse(
                        name.startswith(("tkinter", "infrastructure"))
                        or "system_activity" in name
                        or name in ("storage", "gui"),
                    )


    def test_projections_preserve_original_german_copy(self) -> None:
        stamp = datetime(2026, 10, 12, 13).timestamp()
        context = context_at(stamp)
        state = PetState(satiety=10, mood=55)
        mind = AikoMind(rng=random.Random(7))
        reading = ComputerSnapshot(cpu=82, ram=55, measured_at=1000.0)
        for observing in (False, True):
            with self.subTest(observing=observing):
                hover = project_hover(
                    snapshot_pet(state), context, reading,
                    observe_computer=observing,
                )
                status = project_status(
                    snapshot_pet(state), context,
                    mind.emotion(state, 1000.0), None, reading,
                    observe_computer=observing,
                )
                self.assertEqual(hover.feed_label, "Mittagessen")
                self.assertIn("Montag", hover.header)
                self.assertEqual(
                    status.hint, "Ein kleiner Snack wäre schön ...",
                )
                if observing:
                    self.assertIn("CPU 82 %", hover.hardware_line)
                else:
                    self.assertEqual(
                        status.hardware_line,
                        "Rechnerbeobachtung deaktiviert",
                    )
        preferences = PetSettings(auto_walk=False, spontaneous_talk=False)
        projected = project_settings(preferences)
        self.assertFalse(projected.value("auto_walk"))
        self.assertFalse(projected.value("spontaneous_talk"))

    def test_active_desktop_uses_canonical_monitor_and_view_source(self) -> None:
        for path in ("gui.py", "desktop/lifecycle.py"):
            source = (ROOT / path).read_text("utf-8")
            self.assertNotIn("system_activity import ActivityMonitor", source)
            self.assertIn("infrastructure.hardware.monitor import", source)
        source = (ROOT / "gui.py").read_text("utf-8")
        self.assertIn("DesktopPresentation(", source)
        self.assertNotIn("DesktopViewSource(", source)


if __name__ == "__main__":
    unittest.main()
