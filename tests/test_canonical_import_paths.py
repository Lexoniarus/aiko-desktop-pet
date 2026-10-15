"""Enforce canonical imports after separating pet and desktop UI owners."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"
LEGACY_PACKAGES = frozenset({"personality", "presentation"})
LEGACY_UI_MODULES = frozenset({
    "action_toolbar", "animated_pet", "character_sprite_cache",
    "desktop_window", "food_menu", "food_overlay", "game_speech",
    "hover_contracts", "hover_geometry", "hover_ui",
    "rest_pose_renderer", "rock_paper_scissors_window",
    "settings_contracts", "settings_window", "skin",
    "speech_presenter", "toolbar_details", "window_drag",
})


def active_sources() -> tuple[Path, ...]:
    """Exclude compatibility modules, never the new canonical implementation."""
    paths = []
    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT)
        if relative.parts[0] in LEGACY_PACKAGES:
            continue
        if (
            len(relative.parts) == 2 and relative.parts[0] == "ui"
            and relative.stem in LEGACY_UI_MODULES
        ):
            continue
        paths.append(path)
    return tuple(sorted(paths))


def legacy_target(name: str) -> bool:
    """Reject obsolete imports regardless of whether they are relative."""
    target = name.removeprefix("aiko_pet.")
    top, _, rest = target.partition(".")
    if top in LEGACY_PACKAGES:
        return True
    return (
        top == "ui"
        and rest.partition(".")[0] in LEGACY_UI_MODULES
    )


class CanonicalImportTests(unittest.TestCase):
    def test_new_owners_never_import_old_module_paths(self) -> None:
        for path in active_sources():
            with self.subTest(module=str(path.relative_to(ROOT))):
                tree = ast.parse(path.read_text("utf-8"))
                imports = [
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                ]
                imports.extend(
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                )
                for name in imports:
                    self.assertFalse(
                        legacy_target(name),
                        f"{path.relative_to(ROOT)} imports {name}",
                    )

    def test_pet_mind_never_performs_implicit_file_loading(self) -> None:
        source = (ROOT / "pet/mind/mind.py").read_text("utf-8")
        self.assertNotIn("DialogueBook.from_file(", source)
        self.assertNotIn("CATALOGUE as CATALOGUE", source)
        self.assertIn("self.book = book", source)

    def test_decision_owners_have_precise_method_names(self) -> None:
        from aiko_pet.application.attention import AttentionCoordinator
        from aiko_pet.desktop.animation_runtime import DesktopAnimationRuntime
        from aiko_pet.desktop.session_runtime import DesktopSessionRuntime

        for owner, obsolete in (
            (AttentionCoordinator, "cursor_moved"),
            (AttentionCoordinator, "walk_finished"),
            (AttentionCoordinator, "idle_animation"),
            (DesktopAnimationRuntime, "choose"),
            (DesktopSessionRuntime, "save"),
        ):
            with self.subTest(owner=owner.__name__, method=obsolete):
                self.assertFalse(hasattr(owner, obsolete))

    def test_lifecycle_has_no_module_level_state_mutation_forwarders(
        self,
    ) -> None:
        from aiko_pet.pet import lifecycle

        for old in (
            "advance_pet_time", "apply_daily_routine", "PetTimeline",
            "RoutineActor",
        ):
            with self.subTest(member=old):
                self.assertFalse(hasattr(lifecycle, old))

    def test_friendship_reward_has_no_mutation_adapter(self) -> None:
        from aiko_pet.pet import friendship

        self.assertFalse(hasattr(friendship, "award_friendship_for_care"))
        self.assertTrue(hasattr(friendship, "calculate_friendship_reward"))

    def test_need_decay_only_publishes_pure_calculation(self) -> None:
        from aiko_pet.pet import need_decay

        self.assertFalse(hasattr(need_decay, "apply_need_decay"))
        self.assertTrue(hasattr(need_decay, "calculate_need_decay"))

    def test_care_mutation_has_no_module_level_legacy_adapter(self) -> None:
        from aiko_pet.pet import care_actions

        self.assertFalse(hasattr(care_actions, "apply_care_action"))
        self.assertFalse(hasattr(care_actions, "CareState"))

    def test_time_context_has_no_legacy_localized_display_methods(self) -> None:
        from aiko_pet.pet.routine import TimeContext

        for obsolete in ("label", "schedule_line", "greeting"):
            with self.subTest(member=obsolete):
                self.assertFalse(hasattr(TimeContext, obsolete))

    def test_pet_state_has_no_legacy_mutation_reexports(self) -> None:
        module = __import__("aiko_pet.pet.state", fromlist=["PetState"])
        for obsolete in (
            "apply_care_action", "award_friendship_for_care",
            "apply_need_decay", "advance_pet_time", "apply_daily_routine",
        ):
            with self.subTest(export=obsolete):
                self.assertFalse(hasattr(module, obsolete))

    def test_migration_only_test_filenames_were_retired(self) -> None:
        for old_name in (
            "test_personality_package.py",
            "test_presentation_boundary.py",
        ):
            self.assertFalse((ROOT.parent / "tests" / old_name).exists())

    def test_old_packages_and_ui_alias_modules_were_removed(self) -> None:
        for name in LEGACY_PACKAGES:
            self.assertFalse((ROOT / name).exists())
        for name in LEGACY_UI_MODULES:
            self.assertFalse((ROOT / "ui" / f"{name}.py").exists())

def imported_modules(source: Path) -> tuple[str, ...]:
    """Inspect both regular imports and from-imports without executing code."""
    syntax = ast.parse(source.read_text("utf-8"))
    return tuple(
        node.module or ""
        for node in ast.walk(syntax)
        if isinstance(node, ast.ImportFrom)
    ) + tuple(
        alias.name
        for node in ast.walk(syntax)
        if isinstance(node, ast.Import)
        for alias in node.names
    )


class LegacyBoundaryAuditTests(unittest.TestCase):
    def test_tools_and_all_tests_use_only_canonical_imports(self) -> None:
        tests = ROOT.parent / "tests"
        tools = ROOT.parent / "tools"
        candidates = tuple(tools.glob("*.py")) + tuple(tests.glob("*.py"))
        for path in candidates:
            with self.subTest(module=path.name):
                for module in imported_modules(path):
                    self.assertFalse(
                        legacy_target(module),
                        f"{path.name} imports deprecated {module}",
                    )
