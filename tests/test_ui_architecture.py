"""Architecture guards preventing regression to monolithic desktop ownership."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"

UTILITY_VIEWS = (
    "ui/windows/action_toolbar.py",
    "ui/windows/settings_window.py",
    "ui/windows/toolbar_details.py",
    "ui/common/skin.py",
    "ui/common/window_drag.py",
    "ui/windows/rock_paper_scissors_window.py",
    "ui/windows/hover_ui.py",
    "ui/windows/game_menu.py",
    "ui/windows/game_panel.py",
    "ui/windows/tic_tac_toe_window.py",
    "ui/windows/blackjack_window.py",
)


class UiDependencyRules(unittest.TestCase):
    def test_new_game_rules_and_hand_preserve_dependency_boundaries(self) -> None:
        rule_imports = (
            "tkinter", "ui", "desktop", "pet", "world", "application", "infrastructure",
        )
        for relative, forbidden in (
            ("games/blackjack.py", rule_imports),
            ("games/tic_tac_toe.py", rule_imports),
            ("ui/pet_view/blackjack_hand_presenter.py",
             ("world", "gui", "ctypes", "state")),
        ):
            tree = ast.parse((ROOT / relative).read_text("utf-8"))
            imports = [
                node.module or "" for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            ] + [
                alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                for alias in node.names
            ]
            for module in imports:
                self.assertFalse(set(module.split(".")).intersection(forbidden), module)

    def test_utility_windows_do_not_import_desktop_or_domain(self) -> None:
        forbidden = {
            "gui",
            "domain",
            "adaptive",
            "storage",
            "system_activity",
            "window_stack",
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
                    node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
                }
                self.assertNotIn("DesktopPet", names)

    def test_character_and_native_window_require_only_typed_ports(self) -> None:
        forbidden = {
            "storage",
            "domain",
            "adaptive",
            "adaptive_models",
            "system_activity",
        }
        for relative in (
            "ui/pet_view/animated_pet.py",
            "ui/pet_view/desktop_window.py",
        ):
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

    def test_persistence_never_advances_domain_state(self) -> None:
        for owner in ("infrastructure/persistence.py", "desktop/persistence.py"):
            with self.subTest(owner=owner):
                tree = ast.parse((ROOT / owner).read_text("utf-8"))
                self.assertFalse(
                    any(
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "advance"
                        for node in ast.walk(tree)
                    )
                )

    def test_desktop_runtime_services_do_not_import_domain(self) -> None:
        forbidden = {"gui", "domain", "adaptive", "storage", "dialogue"}
        for relative in (
            "desktop/runtime.py",
            "desktop/maintenance.py",
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
            "infrastructure/hardware/os_sensors.py",
            "infrastructure/hardware/nvidia.py",
            "infrastructure/hardware/sampler.py",
            "infrastructure/hardware/monitor.py",
        )
        for relative in providers:
            with self.subTest(provider=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
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
                self.assertFalse(
                    any(
                        name.startswith(("tkinter", "aiko_pet.ui")) for name in imports
                    ),
                )

    def test_production_text_is_not_read_from_pet_legacy_methods(self) -> None:
        files = (
            "ui/view_models/projections.py",
            "ui/view_models/read_models.py",
            "ui/view_models/text_de.py",
        )
        for relative in files:
            with self.subTest(module=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
                # Inspect Python access, not '.label' inside a localized JSON key.
                accessed = {node.attr for node in ast.walk(tree)
                            if isinstance(node, ast.Attribute)}
                for name in (
                    "status_hint", "feed_label", "schedule_line", "label", "greeting",
                ):
                    self.assertNotIn(name, accessed)

    def test_preference_owner_has_no_dialogue_or_save_implementation(self) -> None:
        source = (ROOT / "desktop/preferences.py").read_text("utf-8")
        tree = ast.parse(source)
        imports = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        self.assertFalse(
            any(
                "storage" in name or "gui" in name or "dialogue" in name
                for name in imports
            )
        )
        self.assertNotIn("DesktopPet", source)
        self.assertIn("class DesktopPreferences:", source)


if __name__ == "__main__":
    unittest.main()
