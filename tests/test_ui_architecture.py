"""Architecture guards preventing regression to monolithic desktop ownership."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"

UTILITY_VIEWS = (
    "ui/action_toolbar.py",
    "ui/status_panel.py",
    "ui/settings_popup.py",
    "ui/hover_ui.py",
)


class UiDependencyRules(unittest.TestCase):
    def test_gui_composition_root_stays_bounded(self) -> None:
        source = (ROOT / "gui.py").read_text("utf-8")
        self.assertLessEqual(
            len(source.splitlines()), 600,
            "Move feature behavior to its owning object rather than gui.py",
        )

    def test_utility_windows_do_not_import_desktop_or_domain(self) -> None:
        forbidden = {
            "gui", "domain", "adaptive", "storage",
            "system_activity", "window_stack",
        }
        for relative in UTILITY_VIEWS:
            with self.subTest(module=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
                imports = [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ]
                for imported in imports:
                    self.assertNotIn(imported.rsplit(".", 1)[-1], forbidden)
                names = {
                    node.id for node in ast.walk(tree)
                    if isinstance(node, ast.Name)
                }
                self.assertNotIn("DesktopPet", names)

    def test_application_never_depends_on_ui_implementations(self) -> None:
        for path in (ROOT / "application").glob("*.py"):
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text("utf-8"))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ImportFrom):
                        continue
                    name = node.module or ""
                    self.assertFalse(
                        name == "ui" or name.startswith("ui.")
                        or name.startswith("aiko_pet.ui."),
                    )

    def test_character_and_native_window_require_only_typed_ports(self) -> None:
        forbidden = {
            "storage", "domain", "adaptive", "adaptive_models",
            "system_activity",
        }
        for relative in ("ui/animated_pet.py", "ui/desktop_window.py"):
            with self.subTest(module=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
                direct = [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ]
                self.assertFalse(
                    forbidden.intersection({
                        name.rsplit(".", 1)[-1] for name in direct
                    }),
                )

    def test_character_does_not_choose_commentary_events(self) -> None:
        source = (ROOT / "ui/animated_pet.py").read_text("utf-8")
        for token in (
            "cursor_far", "cursor_follow", "walk_pause",
            "next_cursor_line", "random.random(",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_hover_uses_public_dragging_contract(self) -> None:
        source = (ROOT / "ui/hover_ui.py").read_text("utf-8")
        self.assertNotIn("toolbar._dragging", source)

    def test_persistence_never_advances_domain_state(self) -> None:
        tree = ast.parse(
            (ROOT / "desktop/persistence.py").read_text("utf-8"),
        )
        self.assertFalse(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "advance"
            for node in ast.walk(tree)
        ))

    def test_desktop_runtime_services_do_not_import_domain(self) -> None:
        forbidden = {"gui", "domain", "adaptive", "storage", "dialogue"}
        for relative in (
            "desktop/runtime.py", "desktop/maintenance.py",
            "desktop/input.py",
        ):
            with self.subTest(module=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
                modules = {
                    (node.module or "").rsplit(".", 1)[-1]
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                }
                self.assertFalse(modules.intersection(forbidden))

    def test_sensor_modules_are_not_tk_or_browser_adapters(self) -> None:
        providers = (
            "infrastructure/hardware/metrics.py",
            "infrastructure/hardware/os_sensors.py",
            "infrastructure/hardware/nvidia.py",
            "infrastructure/hardware/sampler.py",
            "infrastructure/hardware/monitor.py",
        )
        for relative in providers:
            with self.subTest(provider=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
                imports = [
                    node.module or "" for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ] + [
                    alias.name for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                ]
                self.assertFalse(
                    any(name.startswith(("tkinter", "aiko_pet.ui"))
                        for name in imports),
                )

    def test_system_activity_remains_only_compatibility_exports(self) -> None:
        source = (ROOT / "system_activity.py").read_text("utf-8")
        self.assertLessEqual(len(source.splitlines()), 50)
        tree = ast.parse(source)
        self.assertFalse(any(
            isinstance(node, (ast.ClassDef, ast.FunctionDef))
            for node in tree.body
        ))

    def test_application_services_never_import_tkinter(self) -> None:
        for path in (ROOT / "application").glob("*.py"):
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text("utf-8"))
                imported = [
                    name.name for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for name in node.names
                ]
                imported += [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ]
                self.assertFalse(
                    any(name.startswith("tkinter") for name in imported),
                )


if __name__ == "__main__":
    unittest.main()
