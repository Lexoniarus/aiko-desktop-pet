"""Canonical desktop-native and presentation-motion package boundaries."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


from aiko_pet.desktop import (
    geometry,
)

ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"


class NativeDesktopLayoutTests(unittest.TestCase):
    def test_pure_geometry_is_not_an_operating_system_provider(self) -> None:
        state = geometry.TaskbarTrack(100, 900, 760)
        self.assertEqual(state.clamp_x(2000, 128), 772)
        self.assertEqual(state.sprite_y(1), 566)
        tree = ast.parse(
            (ROOT / "desktop/geometry.py").read_text("utf-8"),
        )
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
            name.startswith(("tkinter", "ctypes", "subprocess", "win32"))
            for name in imports
        ))


    def test_presentation_motion_imports_only_pure_geometry(self) -> None:
        for name in ("animation.py", "gaze.py", "movement.py"):
            tree = ast.parse(
                (ROOT / "presentation" / name).read_text("utf-8"),
            )
            imports = [
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            ]
            self.assertFalse(any(
                "window_stack" in module or "global_input" in module
                or module == "taskbar"
                for module in imports
            ))


if __name__ == "__main__":
    unittest.main()
