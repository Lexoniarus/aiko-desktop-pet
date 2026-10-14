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

    def test_legacy_packages_do_not_own_classes(self) -> None:
        for folder in LEGACY_PACKAGES:
            for path in (ROOT / folder).glob("*.py"):
                with self.subTest(path=str(path.relative_to(ROOT))):
                    tree = ast.parse(path.read_text("utf-8"))
                    self.assertFalse(any(
                        isinstance(node, ast.ClassDef)
                        for node in tree.body
                    ))

# Explicit boundary suites deliberately verify that legacy public aliases
# resolve to their one canonical owner. No ordinary behavior suite may rely on
# these imports, so removing a compatibility facade is an isolated decision.
COMPATIBILITY_TESTS = frozenset({
    "test_game_window_ownership.py",
    "test_hover_owner_boundary.py",
    "test_pet_animation_contracts.py",
    "test_pet_animation_policy_boundary.py",
    "test_pet_animation_timing_boundary.py",
    "test_pet_gaze_boundary.py",
    "test_pet_idle_emote_boundary.py",
    "test_pet_item_assets_boundary.py",
    "test_pet_mind_boundary.py",
    "test_pet_movement_boundary.py",
    "test_pet_renderer_ownership.py",
    "test_pet_speech_owner.py",
    "test_pet_view_helpers.py",
    "test_reaction_owner_boundary.py",
    "test_ui_common_boundary.py",
    "test_ui_control_owner_boundary.py",
    "test_ui_skin_boundary.py",
    "test_ui_view_contract_owner.py",
    "test_ui_view_models_owner.py",
    "test_ui_window_contracts_boundary.py",
})


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
    def test_tools_and_regular_tests_use_only_canonical_imports(self) -> None:
        tests = ROOT.parent / "tests"
        tools = ROOT.parent / "tools"
        candidates = tuple(tools.glob("*.py")) + tuple(
            path for path in tests.glob("*.py")
            if path.name not in COMPATIBILITY_TESTS
        )
        for path in candidates:
            with self.subTest(module=path.name):
                for module in imported_modules(path):
                    self.assertFalse(
                        legacy_target(module),
                        f"{path.name} imports deprecated {module}",
                    )
