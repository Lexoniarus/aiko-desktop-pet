"""Static package boundaries and acyclic internal source dependencies."""

from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "aiko_pet"


def module_name(path: Path) -> str:
    parts = path.relative_to(ROOT).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def import_targets(tree: ast.AST, package: str) -> set[str]:
    """Resolve every import form, including from-package submodule imports."""
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            scope = package.split(".")
            up = node.level - 1
            if up >= len(scope):
                continue
            scope = scope[:len(scope) - up] if up else scope
            prefix = ".".join(scope)
            target = (
                f"{prefix}.{node.module}"
                if node.module else prefix
            )
        else:
            target = node.module or ""
        targets.add(target)
        targets.update(f"{target}.{alias.name}" for alias in node.names)
    return targets


def internal_dependencies(
    path: Path, known_modules: frozenset[str],
) -> set[str]:
    """Resolve static imports without importing the app."""
    current = module_name(path)
    package = (
        current if path.stem == "__init__"
        else current.rsplit(".", 1)[0]
    )
    tree = ast.parse(path.read_text("utf-8"), filename=str(path))
    dependencies = import_targets(tree, package) & known_modules
    dependencies.discard(current)
    return dependencies


class PackageDependencyTests(unittest.TestCase):
    def test_boundary_resolver_covers_nested_and_relative_imports(self) -> None:
        for statement in (
            "import aiko_pet.ui as view",
            "from aiko_pet import ui",
            "from ..ui import windows",
            "if True:\n    from .. import ui",
        ):
            with self.subTest(statement=statement):
                targets = import_targets(
                    ast.parse(statement), "aiko_pet.application",
                )
                self.assertIn("aiko_pet.ui", targets)

    def test_layers_only_import_allowed_dependencies(self) -> None:
        outer = tuple(f"aiko_pet.{name}" for name in (
            "ui", "presentation", "desktop", "infrastructure", "storage",
            "system_activity", "gui", "personality", "adaptive", "dialogue",
            "adaptive_models",
        ))
        rules = {
            "application": (*outer, "tkinter"),
            "pet": (*outer, "aiko_pet.application", "aiko_pet.world", "tkinter",
                    "ctypes", "subprocess"),
            "world": (*outer, "aiko_pet.application", "aiko_pet.pet",
                      "aiko_pet.games", "aiko_pet.telemetry", "aiko_pet.config",
                      "aiko_pet.asset_paths", "tkinter", "ctypes", "subprocess"),
            "ui/view_models": (
                "tkinter", "ctypes", "aiko_pet.infrastructure",
                "aiko_pet.desktop", "aiko_pet.storage",
                "aiko_pet.system_activity", "aiko_pet.gui",
            ),
        }
        for layer, forbidden in rules.items():
            for path in (SOURCES / layer).rglob("*.py"):
                with self.subTest(module=str(path.relative_to(SOURCES))):
                    current = module_name(path)
                    package = (current if path.stem == "__init__"
                               else current.rsplit(".", 1)[0])
                    tree = ast.parse(path.read_text("utf-8"))
                    for target in import_targets(tree, package):
                        self.assertFalse(any(
                            target == name or target.startswith(name + ".")
                            for name in forbidden
                        ), f"{current} imports forbidden {target}")
                        if layer == "pet" and target.startswith("aiko_pet.games"):
                            self.assertTrue(
                                target == "aiko_pet.games.contracts"
                                or target.startswith("aiko_pet.games.contracts."),
                                f"{current} may only share immutable game contracts",
                            )

    def test_all_package_modules_import_without_starting_the_desktop(self) -> None:
        for path in SOURCES.rglob("*.py"):
            with self.subTest(module=module_name(path)):
                importlib.import_module(module_name(path))

    def test_all_internal_module_imports_form_an_acyclic_graph(self) -> None:
        files = tuple(SOURCES.rglob("*.py"))
        names = frozenset(module_name(path) for path in files)
        modules = {
            module_name(path): internal_dependencies(path, names)
            for path in files
        }
        visited: set[str] = set()
        in_progress: set[str] = set()
        stack: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in in_progress:
                start = stack.index(name)
                self.fail("Internal import cycle: " +
                          " -> ".join((*stack[start:], name)))
            in_progress.add(name)
            stack.append(name)
            for dependency in sorted(modules.get(name, ())):
                visit(dependency)
            stack.pop()
            in_progress.remove(name)
            visited.add(name)

        for name in sorted(names):
            visit(name)


if __name__ == "__main__":
    unittest.main()
