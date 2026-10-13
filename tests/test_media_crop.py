"""Regress exact Tk window cropping and a single viewport across GIF frames."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.media_crop import (
    CapturedFrame, framed_bounds, save_sequence,
)


class MediaCropTests(unittest.TestCase):
    def test_disconnected_ui_windows_share_small_even_padding(self) -> None:
        bounds = framed_bounds(
            ((40, 35, 105, 94), (130, 60, 205, 133)),
            (280, 190),
        )
        self.assertEqual(bounds, (16, 11, 229, 157))

    def test_taskbar_edge_uses_padding_without_losing_real_pixels(self) -> None:
        image = Image.new("RGB", (240, 180), "#000000")
        ImageDraw.Draw(image).rectangle(
            (60, 80, 180, 179), fill="#90bce7",
        )
        frame = CapturedFrame(image, ((60, 80, 181, 180),))
        self.assertEqual(frame.crop_box, (36, 56, 205, 204))
        cropped = frame.cropped()
        self.assertEqual(cropped.size, (169, 148))
        self.assertEqual(cropped.getpixel((24, 123)), (144, 188, 231))
        self.assertEqual(cropped.getpixel((24, 124)), (0, 0, 0))

    def test_leftmost_toolbar_and_rightmost_bubble_are_both_complete(self) -> None:
        image = Image.new("RGB", (280, 190), "black")
        ImageDraw.Draw(image).rectangle(
            (35, 45, 116, 124), fill="#136abc",
        )
        ImageDraw.Draw(image).rectangle(
            (150, 27, 241, 99), fill="#dbe6f3",
        )
        frame = CapturedFrame(
            image, ((35, 45, 117, 125), (150, 27, 242, 100)),
        )
        cropped = frame.cropped()
        self.assertEqual(cropped.size, (255, 146))
        self.assertEqual(cropped.getpixel((24, 42)), (19, 106, 188))
        self.assertEqual(cropped.getpixel((230, 24)), (219, 230, 243))

    def test_different_gif_cues_keep_one_fixed_crop_rectangle(self) -> None:
        image_a = Image.new("RGB", (280, 190), "black")
        ImageDraw.Draw(image_a).rectangle(
            (42, 38, 106, 90), fill="red",
        )
        image_b = Image.new("RGB", (280, 190), "black")
        ImageDraw.Draw(image_b).rectangle(
            (143, 49, 216, 139), fill="blue",
        )
        frames = (
            CapturedFrame(image_a, ((42, 38, 107, 91),)),
            CapturedFrame(image_b, ((143, 49, 217, 140),)),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sequence.gif"
            save_sequence(frames, (100, 140), path)
            with Image.open(path) as gif:
                self.assertEqual(gif.size, (223, 150))
                self.assertEqual(gif.n_frames, 2)
                gif.seek(1)
                self.assertEqual(gif.size, (223, 150))

    def test_clipped_window_rejected_instead_of_hidden_by_crop(self) -> None:
        for box in ((-1, 30, 100, 100), (30, 30, 281, 100)):
            with self.subTest(box=box):
                with self.assertRaises(ValueError):
                    framed_bounds((box,), (280, 190))

    def test_empty_or_misaligned_gif_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.gif"
            with self.assertRaises(ValueError):
                save_sequence((), (), path)
            frames = (CapturedFrame(
                Image.new("RGB", (120, 100)), ((30, 30, 70, 65),),
            ),)
            with self.assertRaises(ValueError):
                save_sequence(frames, (), path)
            with self.assertRaises(ValueError):
                save_sequence(frames, (0,), path)


if __name__ == "__main__":
    unittest.main()
