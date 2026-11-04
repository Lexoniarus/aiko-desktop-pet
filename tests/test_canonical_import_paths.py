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
    "status_panel", "status_contracts", "settings_popup",
})


def active_sources() -> tuple[Path, ...]:
    """Audit the entire current source tree, without legacy exclusions."""
    return tuple(sorted(ROOT.rglob("*.py")))


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
