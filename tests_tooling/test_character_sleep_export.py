"""Verify the complete HD blanket loop while the sleeping character stays still."""

from __future__ import annotations

import unittest
from typing import cast

from PIL import Image, ImageChops, ImageDraw

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.character_assets import load_character_catalog
from tools.character_sleep_export import build_sleep_cycle


def blanket_top(image: Image.Image, x: int) -> int:
    for y in range(248 if x < 247 else 230, 316):
        r, g, b, alpha = cast(tuple[int, int, int, int], image.getpixel((x, y)))
        if alpha >= 128 and b > r * 1.25 and b > g * 1.6 and b > 45:
            return y
    raise AssertionError(f"Missing blanket column at {x}")


class SleepExportTests(unittest.TestCase):
    def test_only_the_blanket_moves_even_when_the_donor_character_differs(self) -> None:
        rest = Image.new("RGBA", (384, 416), (160, 90, 50, 255))
        raised = Image.new("RGBA", rest.size, (210, 140, 90, 255))
        ImageDraw.Draw(rest).rectangle((237, 270, 345, 310), (10, 30, 140, 255))
        ImageDraw.Draw(raised).rectangle((237, 250, 345, 310), (20, 40, 180, 255))
        cycle = build_sleep_cycle(rest, raised)
        self.assertEqual(len(cycle.frames), 8)
        self.assertEqual(cycle.frames[0].tobytes(), rest.tobytes())
        for frame in cycle.frames:
            unchanged = Image.composite(rest, frame, cycle.mask)
            self.assertEqual(unchanged.tobytes(), rest.tobytes())
        self.assertNotEqual(cycle.frames[4].tobytes(), rest.tobytes())
        for index in (1, 2, 3):
            self.assertEqual(
                cycle.frames[index].tobytes(), cycle.frames[8 - index].tobytes(),
            )
        for index in range(8):
            current, following = cycle.contours[index], cycle.contours[(index + 1) % 8]
            self.assertLessEqual(
                max(abs(a[1] - b[1]) for a, b in zip(current, following)), 8,
            )

    def test_wrong_anchor_size_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_sleep_cycle(Image.new("RGBA", (192, 208)),
                              Image.new("RGBA", (384, 416)))

    def test_shipped_loop_keeps_character_bed_and_anchor_fixed(self) -> None:
        frames = self.shipped_frames()
        rest = frames[0]
        for frame in frames:
            # The entire editable envelope is confined to the blue blanket.
            difference = ImageChops.difference(frame, rest)
            difference.paste((0, 0, 0, 0), (237, 231, 346, 314))
            self.assertEqual(difference.tobytes(), bytes(384 * 416 * 4))
            self.assertEqual(frame.getchannel("A").getbbox(),
                             rest.getchannel("A").getbbox())
            # Within that envelope, all skin/hair/sleeve and wooden bed pixels
            # also retain their original colors, rather than following a warp.
            for x in range(237, 346):
                for y in range(231, 314):
                    pixel = cast(tuple[int, int, int, int], rest.getpixel((x, y)))
                    r, g, b, alpha = pixel
                    character = r > 110 or (g > 40 and g > b * 0.85)
                    wood = r > 40 and r > g * 1.18 and g > b * 1.2
                    if alpha >= 128 and (character or wood):
                        self.assertEqual(frame.getpixel((x, y)), pixel)

    def test_all_eight_contour_transitions_include_a_gentle_loop_join(self) -> None:
        frames = self.shipped_frames()
        tops = [[blanket_top(frame, x) for x in range(237, 346)] for frame in frames]
        steps = [max(abs(a - b) for a, b in zip(tops[i], tops[(i + 1) % 8]))
                 for i in range(8)]
        self.assertLessEqual(max(steps), 6)
        self.assertLessEqual(steps[2], 6)  # Former 02 -> 03 contour jump: 17 px.
        self.assertLessEqual(steps[7], 2)  # Include 07 -> 00 explicitly.
        self.assertGreater(max(steps), 0)
        for index in (1, 2, 3):
            self.assertEqual(frames[index].tobytes(), frames[8 - index].tobytes())

    def test_sleep_order_timing_and_anchor_are_preserved(self) -> None:
        clip = load_character_catalog().clips["sleep"]
        self.assertTrue(clip.loop)
        self.assertEqual(clip.anchor, (96, 195))
        self.assertEqual([frame.file.stem for frame in clip.frames],
                         [f"{index:02d}" for index in range(8)])
        self.assertEqual([frame.duration_ms for frame in clip.frames],
                         [550, 430, 430, 550, 450, 450, 550, 590])

    @staticmethod
    def shipped_frames() -> list[Image.Image]:
        frames = []
        for index in range(8):
            path = ASSET_ROOT / "frames_2x" / "sleep" / f"{index:02d}.png"
            with Image.open(path) as im:
                frames.append(im.convert("RGBA"))
        return frames
