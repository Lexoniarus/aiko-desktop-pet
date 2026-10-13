"""Static package boundaries and acyclic internal source dependencies."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "aiko_pet"

# Old public entrypoints are imports only; active application use cases must
# not depend on presentation, desktop widgets or concrete providers.
COMPATIBILITY_APPLICATION_MODULES = frozenset({
    "hover_projection.py", "status_projection.py",
    "settings_projection.py", "read_models.py", "view_models.py",
})


def module_name(path: Path) -> str:
    parts = path.relative_to(ROOT).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def internal_dependencies(
    path: Path, known_modules: frozenset[str],
) -> set[str]:
    """Resolve static absolute/relative imports without importing the app."""
    current = module_name(path)
    package = (
        current if path.stem == "__init__"
        else current.rsplit(".", 1)[0]
    )
    tree = ast.parse(path.read_text("utf-8"), filename=str(path))
    dependencies: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in known_modules:
                    dependencies.add(alias.name)
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
        if target in known_modules:
            dependencies.add(target)
        # "from package import submodule" is another module dependency.
        for alias in node.names:
            submodule = f"{target}.{alias.name}"
            if submodule in known_modules:
                dependencies.add(submodule)
    dependencies.discard(current)
    return dependencies


class PackageDependencyTests(unittest.TestCase):
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

    def test_compatibility_application_imports_are_explicitly_scoped(
        self,
    ) -> None:
        for path in (SOURCES / "application").glob("*.py"):
            if path.name in COMPATIBILITY_APPLICATION_MODULES:
                continue
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text("utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        name = node.module or ""
                        self.assertFalse(name.startswith((
                            "ui", "presentation", "desktop",
                            "infrastructure", "system_activity",
                        )))
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.assertFalse(alias.name.startswith((
                                "aiko_pet.ui", "aiko_pet.presentation",
                                "aiko_pet.desktop", "aiko_pet.infrastructure",
                            )))

    def test_canonical_pet_and_personality_do_not_import_outer_layers(
        self,
    ) -> None:
        for folder in ("pet", "personality"):
            for path in (SOURCES / folder).glob("*.py"):
                with self.subTest(path=str(path.relative_to(SOURCES))):
                    tree = ast.parse(path.read_text("utf-8"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            name = node.module or ""
                            self.assertFalse(name.startswith((
                                "ui", "presentation", "desktop",
                                "application", "infrastructure",
                            )))
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                self.assertFalse(alias.name.startswith((
                                    "aiko_pet.ui", "aiko_pet.presentation",
                                    "aiko_pet.desktop", "aiko_pet.application",
                                    "aiko_pet.infrastructure",
                                )))


if __name__ == "__main__":
    unittest.main()
