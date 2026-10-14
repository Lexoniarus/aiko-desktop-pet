"""Shared window dragging has one canonical class implementation."""

import unittest

from aiko_pet.ui.common.window_drag import WindowDrag, bounded_position


class CommonWindowBoundaryTests(unittest.TestCase):
    def test_compatibility_exports_reuse_same_objects(self) -> None:
        self.assertEqual(WindowDrag.__module__, "aiko_pet.ui.common.window_drag")
        self.assertEqual(bounded_position.__module__, "aiko_pet.ui.common.window_drag")

