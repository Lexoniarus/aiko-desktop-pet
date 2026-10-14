"""Shared window dragging has one canonical class implementation."""

import unittest

from aiko_pet.ui.common.window_drag import WindowDrag, bounded_position
from aiko_pet.ui.window_drag import WindowDrag as LegacyWindowDrag
from aiko_pet.ui.window_drag import bounded_position as legacy_bounded_position


class CommonWindowBoundaryTests(unittest.TestCase):
    def test_compatibility_exports_reuse_same_objects(self) -> None:
        self.assertIs(WindowDrag, LegacyWindowDrag)
        self.assertIs(bounded_position, legacy_bounded_position)

