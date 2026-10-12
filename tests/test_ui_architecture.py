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

APPLICATION_SERVICES = (
    "application/controller.py",
    "application/router.py",
    "application/activity.py",
    "application/read_models.py",
    "application/inbox.py",
)


class UiDependencyRules(unittest.TestCase):
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

    def test_application_services_never_import_tkinter(self) -> None:
        for relative in APPLICATION_SERVICES:
            with self.subTest(module=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
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
