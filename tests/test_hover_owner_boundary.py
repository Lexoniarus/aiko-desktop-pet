"""Hover window lifecycle has one canonical class after refactor."""

import unittest

from aiko_pet.ui.windows.hover_ui import HoverUi
from aiko_pet.ui.hover_ui import HoverUi as LegacyHoverUi


class HoverOwnerBoundaryTests(unittest.TestCase):
    def test_class_identity(self) -> None:
        self.assertIs(HoverUi, LegacyHoverUi)
