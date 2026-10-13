"""Architectural completion gates for canonical modules and legacy views."""

from __future__ import annotations

import ast
import random
import unittest
from datetime import datetime
from pathlib import Path

from aiko_pet.application.hover_projection import project_hover as old_hover
from aiko_pet.application.read_models import DesktopViewSource
from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.settings_projection import (
    project_settings as old_settings,
)
from aiko_pet.application.status_projection import project_status as old_status
from aiko_pet.personality.adaptive import AdaptiveRoutine
from aiko_pet.personality.mind import AikoMind
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.presentation.legacy import DesktopViewSource as LegacySource
from aiko_pet.presentation.projections import (
    project_hover, project_settings, project_status,
)
from aiko_pet.presentation.read_models import DesktopPresentation
from aiko_pet.telemetry import ComputerSnapshot


ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"
LEGACY_VIEW_PATHS = (
    "application/hover_projection.py",
    "application/status_projection.py",
    "application/settings_projection.py",
    "application/read_models.py",
    "application/view_models.py",
)


class FakeMonitor:
    def __init__(self, snapshot: ComputerSnapshot) -> None:
        self._snapshot = snapshot

    def latest(self) -> ComputerSnapshot:
        return self._snapshot


class FinalArchitectureTests(unittest.TestCase):
    def test_legacy_ui_modules_only_reexport_canonical_owners(self) -> None:
        for path in LEGACY_VIEW_PATHS:
            with self.subTest(module=path):
                tree = ast.parse((ROOT / path).read_text("utf-8"))
                self.assertFalse(any(
                    isinstance(node, (ast.ClassDef, ast.FunctionDef))
                    for node in tree.body
                ))
                imported = [
                    node.module or ""
                    for node in tree.body
                    if isinstance(node, ast.ImportFrom)
                ]
                self.assertTrue(any(
                    name.startswith("presentation.") for name in imported
                ))

    def test_active_application_has_no_outer_layer_imports(self) -> None:
        ignored = {Path(name).name for name in LEGACY_VIEW_PATHS}
        forbidden = (
            "presentation", "ui", "desktop",
            "infrastructure", "storage", "system_activity",
        )
        for path in (ROOT / "application").glob("*.py"):
            if path.name in ignored:
                continue
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

    def test_legacy_view_source_uses_single_presentation_implementation(
        self,
    ) -> None:
        self.assertIs(DesktopViewSource, LegacySource)
        self.assertTrue(issubclass(DesktopViewSource, DesktopPresentation))
        state = PetState(energy=46)
        settings = PetSettings(x=210, y=480, scale=2)
        mind = AikoMind(rng=random.Random(12))
        adaptive = AdaptiveRoutine()
        reading = ComputerSnapshot(cpu=83, measured_at=1000.0)
        monitor = FakeMonitor(reading)
        def context():
            return context_at(datetime(2026, 10, 12, 13).timestamp())

        def sprite_size():
            return 256, 416

        old = DesktopViewSource(
            state, settings, mind, adaptive, monitor,
            context=context, sprite_size=sprite_size,
        )
        current = DesktopPresentation(
            state, settings, mind, adaptive, monitor,
            context=context, sprite_size=sprite_size,
        )
        self.assertIs(old.state, state)
        self.assertIs(old.settings, settings)
        self.assertIs(old.mind, mind)
        self.assertIs(old.adaptive, adaptive)
        self.assertIs(old.monitor, monitor)
        self.assertEqual(old.hover(), current.hover())
        self.assertEqual(old.status(), current.status())
        self.assertEqual(old.settings_view(), current.settings_view())
        self.assertEqual(old.anchor(), current.anchor())

    def test_old_projectors_agree_with_presentation_and_original_copy(
        self,
    ) -> None:
        stamp = datetime(2026, 10, 12, 13).timestamp()
        context = context_at(stamp)
        state = PetState(satiety=10, mood=55)
        mind = AikoMind(rng=random.Random(7))
        reading = ComputerSnapshot(cpu=82, ram=55, measured_at=1000.0)
        for observing in (False, True):
            with self.subTest(observing=observing):
                hover = old_hover(
                    state, context, reading, observe_computer=observing,
                )
                self.assertEqual(hover, project_hover(
                    snapshot_pet(state), context, reading,
                    observe_computer=observing,
                ))
                status = old_status(
                    state, context, mind, None, reading,
                    now=1000.0, observe_computer=observing,
                )
                self.assertEqual(status, project_status(
                    snapshot_pet(state), context,
                    mind.emotion(state, 1000.0), None, reading,
                    observe_computer=observing,
                ))
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
        self.assertEqual(old_settings(preferences), project_settings(preferences))
        self.assertFalse(old_settings(preferences).value("auto_walk"))

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
