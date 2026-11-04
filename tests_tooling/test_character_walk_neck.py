"""Walking collar fitting preserves the approved head and visible clothing."""

from __future__ import annotations

import unittest

from PIL import Image, ImageDraw, ImageOps

from tools.character_neck_join_export import protected_pixels
from tools.character_walk_neck import fit_walk_neck, rgba_pixel


class WalkNeckTests(unittest.TestCase):
    def components(self, side: str = "right") -> tuple[Image.Image, ...]:
        head = Image.new("RGBA", (384, 416))
        draw = ImageDraw.Draw(head)
        draw.rectangle((170, 215, 208, 239), fill=(255, 224, 207, 255))
        draw.rectangle((179, 240, 192, 244), fill=(249, 174, 154, 255))
        draw.line((211, 248, 213, 250), fill=(14, 20, 26, 255))
        # A detached turquoise hair tip is artwork, not a dark cut remnant.
        draw.point((218, 248), fill=(10, 161, 183, 255))
        body = Image.new("RGBA", head.size)
        draw = ImageDraw.Draw(body)
        draw.polygon(((169, 244), (209, 258), (219, 300), (160, 300)),
                     fill=(40, 61, 126, 255))
        if side == "left":
            head, body = ImageOps.mirror(head), ImageOps.mirror(body)
        return Image.alpha_composite(head, body), head, body

    def test_each_side_preserves_jaw_clothing_and_art_outside_join(self) -> None:
        for side in ("left", "right"):
            with self.subTest(side=side):
                current, head, body = self.components(side)
                result = fit_walk_neck(current, head, body, anchor=240, side=side)
                self.assertEqual(protected_pixels(current), protected_pixels(result))
                self.assertEqual(current.crop((0, 0, 384, 240)).tobytes(),
                                 result.crop((0, 0, 384, 240)).tobytes())
                for y in range(240, 259):
                    for x in range(165, 231):
                        if rgba_pixel(body, (x, y))[3]:
                            self.assertEqual(result.getpixel((x, y)),
                                             body.getpixel((x, y)))
                self.assertEqual(set(result.getchannel("A").tobytes()), {0, 255})

    def test_fits_to_phase_collar_instead_of_retaining_hanging_cut(self) -> None:
        current, head, body = self.components()
        result = fit_walk_neck(current, head, body, anchor=240, side="right")
        # The old source ends at y244; the collar is lower at the front neck.
        self.assertEqual(rgba_pixel(current, (188, 247))[3], 0)
        self.assertEqual(rgba_pixel(result, (188, 247))[3], 255)
        skin = {(x, y) for y in range(240, 259) for x in range(165, 231)
                if rgba_pixel(result, (x, y))[0] > 200}
        self.assertTrue(skin)
        touching = {p for p in skin if any(
            rgba_pixel(body, (p[0] + dx, p[1] + dy))[3] >= 128
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )}
        reached = set(touching)
        pending = list(touching)
        while pending:
            x, y = pending.pop()
            for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if point in skin and point not in reached:
                    reached.add(point)
                    pending.append(point)
        self.assertEqual(reached, skin)

    def test_removes_dark_detached_cut_but_retains_hair_tip(self) -> None:
        current, head, body = self.components()
        result = fit_walk_neck(current, head, body, anchor=240, side="right")
        self.assertEqual(rgba_pixel(result, (212, 249))[3], 0)
        self.assertEqual(result.getpixel((218, 248)), head.getpixel((218, 248)))

    def test_invalid_source_aborts_without_mutating_inputs(self) -> None:
        current, head, body = self.components()
        before = [im.tobytes() for im in (current, head, body)]
        with self.assertRaisesRegex(ValueError, "No collar"):
            fit_walk_neck(current, head, Image.new("RGBA", head.size),
                          anchor=240, side="right")
        self.assertEqual([im.tobytes() for im in (current, head, body)], before)
