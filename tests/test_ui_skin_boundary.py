"""Shared widgets use one canonical Tk skin implementation."""

import unittest

from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.skin import AikoSkin as LegacySkin


class UiSkinBoundaryTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        self.assertIs(AikoSkin, LegacySkin)
