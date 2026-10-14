"""Hover window lifecycle has one canonical class after refactor."""

import unittest

from aiko_pet.ui.windows.hover_ui import HoverUi


class HoverOwnerBoundaryTests(unittest.TestCase):
    def test_class_identity(self) -> None:
        self.assertEqual(HoverUi.__module__, "aiko_pet.ui.windows.hover_ui")
