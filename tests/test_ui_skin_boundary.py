"""Shared widgets use one canonical Tk skin implementation."""

import unittest

from aiko_pet.ui.common.skin import AikoSkin


class UiSkinBoundaryTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        self.assertEqual(AikoSkin.__module__, "aiko_pet.ui.common.skin")
