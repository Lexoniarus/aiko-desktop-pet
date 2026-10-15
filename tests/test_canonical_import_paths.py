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
