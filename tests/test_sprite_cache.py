"""Tk-scaled frame cache never blocks the size toggle with 112 zooms."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.ui.pet_view.character_sprite_cache import CharacterSpriteCache


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
        self.addCleanup(self.cache.close)

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


    def test_hd_frame_is_preferred_when_present(self) -> None:
        """An authored 2x frame is shown as-is, not a nearest-neighbor zoom."""
        sprites = self.cache.for_scale(2)
        clip = sprites["idle"]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "00.png"
            hd = tk.PhotoImage(master=self.root, width=384, height=416)
            hd.put("#334455", to=(90, 50, 105, 65))
            hd.write(str(target), format="png")
            original = clip._hd_paths
            clip._hd_paths = (target, *original[1:])
            try:
                image = clip[0]
                self.assertEqual((image.width(), image.height()), (384, 416))
                self.assertEqual(image.get(92, 52), (51, 68, 85))
                self.assertIs(image, clip[0])
                self.assertEqual(self.cache.for_scale(1)["idle"][0].width(), 192)
            finally:
                clip._hd_paths = original

    def test_bad_hd_geometry_is_rejected(self) -> None:
        clip = self.cache.for_scale(2)["pick_up"]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "00.png"
            wrong = tk.PhotoImage(master=self.root, width=383, height=416)
            wrong.write(str(target), format="png")
            old = clip._hd_paths
            clip._hd_paths = (target, *old[1:])
            try:
                with self.assertRaisesRegex(ValueError, "Invalid HD sprite"):
                    _ = clip[0]
            finally:
                clip._hd_paths = old



if __name__ == "__main__":
    unittest.main()
