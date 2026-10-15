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
)


class UiDependencyRules(unittest.TestCase):
    def test_gui_composition_root_stays_bounded(self) -> None:
        source = (ROOT / "gui.py").read_text("utf-8")
        self.assertLessEqual(
            len(source.splitlines()), 625,
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

    def test_application_never_imports_concrete_persistence(self) -> None:
        for path in (ROOT / "application").glob("*.py"):
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text("utf-8"))
                imported = [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ] + [
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                ]
                self.assertNotIn("storage", imported)
                self.assertNotIn("aiko_pet.storage", imported)

    def test_state_store_cannot_advance_pet_time(self) -> None:
        tree = ast.parse((ROOT / "infrastructure/persistence.py").read_text("utf-8"))
        self.assertFalse(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "advance"
            for node in ast.walk(tree)
        ))

    def test_character_and_native_window_require_only_typed_ports(self) -> None:
        forbidden = {
            "storage", "domain", "adaptive", "adaptive_models",
            "system_activity",
        }
        for relative in ("ui/pet_view/animated_pet.py", "ui/pet_view/desktop_window.py"):
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
        source = (ROOT / "ui/pet_view/animated_pet.py").read_text("utf-8")
        for token in (
            "cursor_far", "cursor_follow", "walk_pause",
            "next_cursor_line", "random.random(",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_hover_uses_public_dragging_contract(self) -> None:
        source = (ROOT / "ui/windows/hover_ui.py").read_text("utf-8")
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


    def test_domain_policies_never_call_pet_private_methods(self) -> None:
        forbidden = {
            "_roll_meals", "_apply_clock", "_decay", "_credit_friendship",
        }
        for relative in (
            "pet/care_actions.py", "pet/friendship.py",
            "pet/need_decay.py", "pet/lifecycle.py",
        ):
            with self.subTest(policy=relative):
                tree = ast.parse((ROOT / relative).read_text("utf-8"))
                calls = {
                    node.func.attr
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                }
                self.assertFalse(calls.intersection(forbidden))

    def test_pet_aggregate_does_not_call_mutating_legacy_adapters(self) -> None:
        source = (ROOT / "pet/state.py").read_text("utf-8")
        tree = ast.parse(source)
        state = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PetState"
        )
        calls = {
            node.func.id
            for node in ast.walk(state)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
        }
        forbidden = {
            "apply_care_action", "apply_need_decay",
            "award_friendship_for_care", "advance_pet_time",
        }
        self.assertFalse(calls.intersection(forbidden))
        for policy in (
            "plan_care_action", "calculate_need_decay",
            "calculate_friendship_reward", "plan_pet_time",
            "calculate_daily_routine",
        ):
            with self.subTest(policy=policy):
                self.assertIn(policy, calls)

    def test_live_desktop_uses_presentation_boundary(self) -> None:
        source = (ROOT / "gui.py").read_text("utf-8")
        self.assertIn("from .ui.view_models.read_models import", source)
        self.assertIn("DesktopPresentation(", source)
        self.assertNotIn("from .application.read_models import", source)

    def test_application_runtime_does_not_import_hardware_provider(self) -> None:
        for module in (
            "activity.py", "attention.py", "ports.py", "read_snapshot.py",
        ):
            with self.subTest(module=module):
                tree = ast.parse(
                    (ROOT / "application" / module).read_text("utf-8"),
                )
                names = [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ]
                self.assertFalse(any(
                    "infrastructure" in name
                    or "system_activity" in name
                    or "presentation" in name
                    or ".ui." in name
                    for name in names
                ))

    def test_pure_policies_and_views_do_not_import_tk_or_storage(self) -> None:
        for owner in ("ui/view_models", "pet/animation", "pet/movement"):
            for module in (ROOT / owner).glob("*.py"):
                with self.subTest(module=str(module.relative_to(ROOT))):
                    tree = ast.parse(module.read_text("utf-8"))
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
                    self.assertFalse(any(
                        name.startswith("tkinter") or name.endswith("storage")
                        or "infrastructure" in name
                        for name in imports
                    ))

    def test_production_text_is_not_read_from_pet_legacy_methods(self) -> None:
        files = (
            "ui/view_models/projections.py",
            "ui/view_models/read_models.py",
            "ui/view_models/text_de.py",
        )
        for relative in files:
            with self.subTest(module=relative):
                source = (ROOT / relative).read_text("utf-8")
                for expression in (
                    ".mood_hint(", ".feed_label(", ".schedule_line",
                    ".label", ".greeting(",
                ):
                    self.assertNotIn(expression, source)


    def test_runtime_consumes_named_ports_not_legacy_private_stages(self) -> None:
        source = (ROOT / "desktop/runtime.py").read_text("utf-8")
        self.assertIn("class DesktopTickPorts:", source)
        self.assertIn("ports.advance_lifecycle(", source)
        self.assertIn("ports.render_character(", source)
        for legacy in (
            "stages._advance_pet_lifecycle", "stages._refresh_hover",
            "stages._render_current_sprite", "stages._closed",
        ):
            with self.subTest(method=legacy):
                self.assertNotIn(legacy, source)

    def test_dead_desktop_shell_input_forwarders_are_removed(self) -> None:
        syntax = ast.parse((ROOT / "gui.py").read_text("utf-8"))
        shell = next(
            node for node in syntax.body
            if isinstance(node, ast.ClassDef) and node.name == "DesktopPet"
        )
        declared = {
            node.name for node in shell.body
            if isinstance(node, ast.FunctionDef)
        }
        old = {
            "_setup_events", "_react_to_click", "_on_tk_press",
            "_on_focus_out", "_dismiss_after_focus_loss", "_show_menu",
            "_poll_desktop_click", "_idle_emote",
        }
        self.assertFalse(declared.intersection(old))

    def test_desktop_gui_wires_runtime_without_self_as_stage_object(self) -> None:
        source = (ROOT / "gui.py").read_text("utf-8")
        self.assertIn("DesktopTickPorts(", source)
        self.assertIn("DesktopPreferences(", source)
        self.assertNotIn("DesktopRuntime(\n            self,", source)
        self.assertNotIn("self.settings.always_on_top =", source)
        self.assertNotIn("self.settings.auto_routine =", source)
        self.assertNotIn("self._window.resize()", source)

    def test_preference_owner_has_no_dialogue_or_save_implementation(self) -> None:
        source = (ROOT / "desktop/preferences.py").read_text("utf-8")
        tree = ast.parse(source)
        imports = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        self.assertFalse(any(
            "storage" in name or "gui" in name
            or "dialogue" in name
            for name in imports
        ))
        self.assertNotIn("DesktopPet", source)
        self.assertIn("class DesktopPreferences:", source)

    def test_input_owns_and_cancels_delayed_focus_callbacks(self) -> None:
        input_source = (ROOT / "desktop/input.py").read_text("utf-8")
        lifecycle = (ROOT / "desktop/lifecycle.py").read_text("utf-8")
        self.assertIn("self._focus_timers", input_source)
        self.assertIn("self.root.after_cancel(", input_source)
        self.assertIn("self._inputs.stop()", lifecycle)

    def test_personality_code_has_no_ui_storage_or_native_imports(self) -> None:
        for path in (ROOT / "pet/mind").glob("*.py"):
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text("utf-8"))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ImportFrom):
                        continue
                    imported = node.module or ""
                    if node.level >= 2:
                        self.assertNotIn(
                            imported.split(".", 1)[0],
                            {"ui", "presentation", "desktop", "storage",
                             "infrastructure"},
                        )
                names = {
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                self.assertFalse(any(
                    name.startswith(("tkinter", "ctypes", "subprocess"))
                    for name in names
                ))

    def test_application_uses_canonical_personality_modules(self) -> None:
        for path in (ROOT / "application").glob("*.py"):
            with self.subTest(module=path.name):
                source = path.read_text("utf-8")
                for original in (
                    "from ..adaptive import", "from ..dialogue import",
                    "from ..adaptive_models import",
                ):
                    self.assertNotIn(original, source)

    def test_native_desktop_adapters_are_not_owned_by_sprite_code(self) -> None:
        sprite = (ROOT / "ui/pet_view/animated_pet.py").read_text("utf-8")
        desktop_window = (ROOT / "ui/pet_view/desktop_window.py").read_text("utf-8")
        driver = (ROOT / "desktop/walk_runtime.py").read_text("utf-8")
        self.assertIn("from ..pet.movement import", driver)
        self.assertIn("WalkConditions(", driver)
        self.assertNotIn("WalkConditions(", sprite)
        self.assertNotIn("WalkDriver(", sprite)
        self.assertNotIn("from .walk_driver import", sprite)
        self.assertNotIn("gaze_direction(", sprite)
        self.assertNotIn("monitor.latest()", sprite)
        self.assertIn("from ...desktop.geometry import FOOT_BASELINE", sprite)
        self.assertIn("from ...desktop.taskbar import", desktop_window)
        self.assertNotIn("from ..taskbar import", sprite)
        self.assertNotIn("from ..taskbar import", desktop_window)


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
