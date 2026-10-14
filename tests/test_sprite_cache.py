"""Tk-scaled frame cache never blocks the size toggle with 112 zooms."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.ui.character_sprite_cache import CharacterSpriteCache


class SpriteCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Graphical display required") from error
        root.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.cache = CharacterSpriteCache(self.root, load_character_catalog())

    def test_only_requested_frames_are_zoomed_and_reused(self) -> None:
        sprites_1x = self.cache.for_scale(1)
        sprites_2x = self.cache.for_scale(2)
        clip = sprites_2x["idle"]
        self.assertEqual(len(clip), 8)
        self.assertEqual(len(getattr(clip, "_zoomed")), 0)
        zoomed = clip[0]
        self.assertEqual(zoomed.width(), 384)
        self.assertEqual(zoomed.height(), 416)
        self.assertEqual(len(getattr(clip, "_zoomed")), 1)
        self.assertIs(zoomed, clip[0])
        self.assertIs(sprites_2x, self.cache.for_scale(2))
        self.assertEqual(sprites_1x["idle"][0].width(), 192)
        self.assertEqual(len(getattr(clip, "_zoomed")), 1)


if __name__ == "__main__":
    unittest.main()
