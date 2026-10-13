"""Canonical desktop-native and presentation-motion package boundaries."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from aiko_pet import animation, desktop_input, gaze, movement, taskbar
from aiko_pet import window_stack
from aiko_pet.desktop import (
    geometry, global_input, taskbar as native_taskbar,
    window_stack as native_stack,
)
from aiko_pet.presentation import (
    animation as sprite_animation,
    gaze as sprite_gaze,
    movement as walk_policy,
)

ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"


class NativeDesktopLayoutTests(unittest.TestCase):
    def test_old_win32_and_input_imports_keep_identity(self) -> None:
        self.assertIs(taskbar.TaskbarTrack, geometry.TaskbarTrack)
        self.assertIs(taskbar.choose_track, native_taskbar.choose_track)
        self.assertIs(taskbar.locate_primary_taskbar,
                      native_taskbar.locate_primary_taskbar)
        self.assertIs(window_stack.WindowStack, native_stack.WindowStack)
        self.assertIs(window_stack.WindowsWindowOps, native_stack.WindowsWindowOps)
        self.assertIs(window_stack._Rect, native_stack._Rect)
        self.assertIs(desktop_input.GlobalMouseClicks, global_input.GlobalMouseClicks)
        self.assertIs(desktop_input.idle_seconds_windows,
                      global_input.idle_seconds_windows)

    def test_sprite_and_walk_policies_are_single_implementations(self) -> None:
        self.assertIs(animation.FrameClock, sprite_animation.FrameClock)
        self.assertIs(animation.choose_passive_animation,
                      sprite_animation.choose_passive_animation)
        self.assertIs(gaze.gaze_sector, sprite_gaze.gaze_sector)
        self.assertIs(movement.WalkController, walk_policy.WalkController)
        self.assertIs(movement.WalkConditions, walk_policy.WalkConditions)

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

    def test_historical_root_modules_remain_adapter_only(self) -> None:
        paths = (
            "taskbar.py", "desktop_input.py", "window_stack.py",
            "animation.py", "gaze.py", "movement.py",
        )
        for path in paths:
            with self.subTest(module=path):
                tree = ast.parse((ROOT / path).read_text("utf-8"))
                self.assertFalse(any(
                    isinstance(node, (ast.ClassDef, ast.FunctionDef))
                    for node in tree.body
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
