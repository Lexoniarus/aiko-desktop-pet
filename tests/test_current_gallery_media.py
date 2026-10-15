"""Validate current screenshots and gifs without imaging dependencies."""

from __future__ import annotations

import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "vorschau"
STILLS = ("Hover",)
ANIMATIONS = {
    "Aiko_Current_Reaction_Sequence.gif",
    "Aiko_Current_Animations.gif",
    "Aiko_Current_Ambient_Blink_And_Glance.gif",
}


class CurrentGalleryTests(unittest.TestCase):
    def test_all_current_tk_stills_have_actual_capture_dimensions(self) -> None:
        for name in STILLS:
            path = PREVIEW / f"Aiko_Current_{name}.png"
            with self.subTest(file=path.name):
                sample = path.read_bytes()
                self.assertGreater(len(sample), 15_000)
                self.assertEqual(sample[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", sample[16:24])
                # No fixed desktop rectangle; every mapped Tk window is
                # fully framed with 24px breathing room, without resampling.
                self.assertGreaterEqual(width, 250)
                self.assertLessEqual(width, 1150)
                self.assertGreaterEqual(height, 290)
                self.assertLessEqual(height, 740)

    def test_reaction_and_112_pose_gifs_have_real_multiple_frames(self) -> None:
        for name in ANIMATIONS:
            path = PREVIEW / name
            with self.subTest(file=name):
                sample = path.read_bytes()
                self.assertGreater(len(sample), 40_000)
                self.assertEqual(sample[:6], b"GIF89a")
                width, height = struct.unpack("<HH", sample[6:10])
                if name == "Aiko_Current_Animations.gif":
                    self.assertEqual((width, height), (224, 246))
                else:
                    self.assertGreaterEqual(width, 200)
                    self.assertLessEqual(width, 1030)
                    self.assertGreaterEqual(height, 230)
                    self.assertLessEqual(height, 740)
                frames = sample.count(b"\x21\xf9\x04")
                minimum = (
                    80 if name == "Aiko_Current_Animations.gif"
                    else 20 if "Ambient" in name else 4
                )
                self.assertGreaterEqual(frames, minimum)

    def test_public_gallery_contains_exactly_the_six_readme_media(self) -> None:
        expected = ANIMATIONS | {
            "Aiko_Current_Hover.png", "Aiko_RPS_Aufgedeckt.png",
            "Aiko_RPS_Spielablauf.gif",
        }
        actual = {path.name for path in PREVIEW.iterdir() if path.is_file()}
        self.assertEqual(actual, expected)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for filename in expected:
            self.assertIn(f"vorschau/{filename}", readme)


if __name__ == "__main__":
    unittest.main()
