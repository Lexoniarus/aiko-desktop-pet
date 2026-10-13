"""Validate actual application media stored in the feature gallery.

These captures are generated from the running Tk desktop pet under Xvfb,
not synthetic mockups or native Windows screen recordings.
"""

from __future__ import annotations

import struct
import unittest
from pathlib import Path


MEDIA = Path(__file__).resolve().parents[1] / "vorschau"
STILLS = (
    "Aiko_RPS_Start.png",
    "Aiko_RPS_Aufgedeckt.png",
    "Aiko_RPS_Punktestand.png",
)
GIF = "Aiko_RPS_Spielablauf.gif"


class RockPaperScissorsMediaTests(unittest.TestCase):
    def test_all_game_stills_have_expected_image_dimensions(self) -> None:
        for name in STILLS:
            with self.subTest(name=name):
                data = (MEDIA / name).read_bytes()
                self.assertGreater(len(data), 10_000)
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", data[16:24])
                self.assertGreaterEqual(width, 880)
                self.assertLessEqual(width, 1040)
                self.assertGreaterEqual(height, 510)
                self.assertLessEqual(height, 650)

    def test_animation_is_a_real_multiframe_gif(self) -> None:
        data = (MEDIA / GIF).read_bytes()
        self.assertGreater(len(data), 30_000)
        self.assertIn(data[:6], (b"GIF87a", b"GIF89a"))
        width, height = struct.unpack("<HH", data[6:10])
        self.assertGreaterEqual(width, 880)
        self.assertLessEqual(width, 1040)
        self.assertGreaterEqual(height, 510)
        self.assertLessEqual(height, 650)
        self.assertGreaterEqual(data.count(b"\x21\xf9\x04"), 8)

    def test_reveal_and_session_score_are_distinct_captures(self) -> None:
        files = [(MEDIA / name).read_bytes() for name in STILLS]
        self.assertEqual(len(set(files)), len(STILLS))


if __name__ == "__main__":
    unittest.main()
