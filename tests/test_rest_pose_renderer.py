"""Tk tests for pose-relative micro-motion with feet fixed in place."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.ui.pet_view.rest_pose_renderer import RestPoseRenderer


class RestPoseRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No graphical display available") from error
        root.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.render = RestPoseRenderer(self.root)
        self.addCleanup(self.root.destroy)

    def test_head_sways_but_leg_pixels_remain_stationary(self) -> None:
        original = tk.PhotoImage(master=self.root, width=192, height=208)
        original.put("#ff0000", to=(85, 40, 106, 105))
        original.put("#00ff00", to=(85, 181, 106, 202))
        moved = self.render.resolve(original, offset=1, scale=1)
        self.assertIsNot(moved, original)
        self.assertTrue(moved.transparency_get(85, 55))
        self.assertFalse(moved.transparency_get(87, 55))
        self.assertEqual(moved.get(87, 55), (255, 0, 0))
        for point in ((85, 182), (105, 200), (0, 180)):
            self.assertEqual(moved.get(*point), original.get(*point))
            self.assertEqual(
                moved.transparency_get(*point),
                original.transparency_get(*point),
            )

    def test_scaled_sprite_scales_only_the_tiny_head_offset(self) -> None:
        for scale in (1, 2):
            with self.subTest(scale=scale):
                original = tk.PhotoImage(
                    master=self.root,
                    width=192 * scale, height=208 * scale,
                )
                original.put(
                    "#ff0000",
                    to=(85 * scale, 40 * scale, 106 * scale, 105 * scale),
                )
                original.put(
                    "#00ff00",
                    to=(85 * scale, 181 * scale, 106 * scale, 202 * scale),
                )
                moved = self.render.resolve(
                    original, offset=-1, scale=scale,
                )
                self.assertTrue(moved.transparency_get(
                    105 * scale, 75 * scale,
                ))
                self.assertFalse(moved.transparency_get(
                    104 * scale, 75 * scale,
                ))
                self.assertEqual(
                    moved.get(91 * scale, 190 * scale),
                    original.get(91 * scale, 190 * scale),
                )

    def test_original_images_and_cache_are_not_modified(self) -> None:
        original = tk.PhotoImage(master=self.root, width=192, height=208)
        original.put("#ff0000", to=(85, 50, 110, 70))
        self.assertIs(self.render.resolve(original, offset=0, scale=1), original)
        variant = self.render.resolve(original, offset=1, scale=1)
        self.assertIs(
            self.render.resolve(original, offset=1, scale=1), variant,
        )
        self.assertEqual(original.get(85, 55), (255, 0, 0))
        self.render.clear()
        other = self.render.resolve(original, offset=1, scale=1)
        self.assertIsNot(other, variant)

    def test_rejects_out_of_range_motion_or_wrong_dimensions(self) -> None:
        original = tk.PhotoImage(master=self.root, width=192, height=208)
        for value in (2, -2):
            with self.assertRaises(ValueError):
                self.render.resolve(original, offset=value, scale=1)
        with self.assertRaises(ValueError):
            self.render.resolve(original, offset=1, scale=3)
        bad = tk.PhotoImage(master=self.root, width=191, height=208)
        with self.assertRaises(ValueError):
            self.render.resolve(bad, offset=1, scale=1)


if __name__ == "__main__":
    unittest.main()
