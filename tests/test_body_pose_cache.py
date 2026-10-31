"""Optional HD body poses stay lazy and share their images across clips."""

from __future__ import annotations

import tkinter as tk
import unittest
from unittest.mock import patch

from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.ui.pet_view.body_pose_cache import BodyPoseCache


class BodyPoseCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Graphical display required") from error
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.cache = BodyPoseCache(self.root, load_character_catalog())
        self.addCleanup(self.cache.close)

    def test_views_are_lazy_and_reuse_the_shared_frontal_frame_at_both_sizes(self):
        with patch("aiko_pet.ui.pet_view.body_pose_cache.tk.PhotoImage",
                   wraps=tk.PhotoImage) as photo:
            native = self.cache.for_scale(2)
            small = self.cache.for_scale(1)
            photo.assert_not_called()
            first = native["body-turn-left"][0]
            self.assertEqual((first.width(), first.height()), (384, 416))
            self.assertIs(first, native["body-turn-right"][0])
            self.assertEqual(photo.call_count, 1)
            scaled = small["body-turn-left"][0]
            self.assertEqual((scaled.width(), scaled.height()), (192, 208))
            self.assertIs(scaled, small["body-turn-right"][0])

    def test_clear_invalidates_images_in_existing_views(self) -> None:
        frames = self.cache.for_scale(2)["body-look-left"]
        first = frames[4]
        self.cache.clear()
        self.assertIsNot(first, frames[4])
        self.assertEqual(first.width(), frames[4].width())
