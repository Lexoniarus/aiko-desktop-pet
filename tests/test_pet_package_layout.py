"""The pet package owns domain rules without outer-layer dependencies."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path




ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"


class PetPackageTests(unittest.TestCase):
    def test_pet_package_has_no_gui_application_or_storage_import(self) -> None:
        for file in (ROOT / "pet").glob("*.py"):
            tree = ast.parse(file.read_text("utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertLessEqual(
                        node.level, 1,
                        f"{file.name} must not escape the pet context",
                    )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertFalse(
                            alias.name.startswith(("tkinter", "aiko_pet.ui")),
                        )


if __name__ == "__main__":
    unittest.main()
