"""Validate current screenshots and gifs without imaging dependencies."""

from __future__ import annotations

import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "vorschau"
STILLS = (
    "Hover", "Hover_Moved", "Dialog",
    "Reaction_Emote_Start", "Reaction_First_Line",
    "Reaction_Followup", "Reaction_Emote_End",
    "Status", "Settings", "Care_Pet", "Care_Feed", "Care_Sleep",
)
ANIMATIONS = {
    "Aiko_Current_Reaction_Sequence.gif": (1160, 768),
    "Aiko_Current_Animations.gif": (224, 246),
}


class CurrentGalleryTests(unittest.TestCase):
    def test_all_current_tk_stills_have_actual_capture_dimensions(self) -> None:
        for name in STILLS:
            path = PREVIEW / f"Aiko_Current_{name}.png"
            with self.subTest(file=path.name):
                sample = path.read_bytes()
                self.assertGreater(len(sample), 15_000)
                self.assertEqual(sample[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(
                    struct.unpack(">II", sample[16:24]), (1160, 768),
                )

    def test_reaction_and_112_pose_gifs_have_real_multiple_frames(self) -> None:
        for name, size in ANIMATIONS.items():
            path = PREVIEW / name
            with self.subTest(file=name):
                sample = path.read_bytes()
                self.assertGreater(len(sample), 40_000)
                self.assertEqual(sample[:6], b"GIF89a")
                self.assertEqual(struct.unpack("<HH", sample[6:10]), size)
                frames = sample.count(b"\x21\xf9\x04")
                self.assertGreaterEqual(
                    frames, 4 if "Reaction" in name else 80,
                )

    def test_all_new_stills_are_distinct(self) -> None:
        payloads = [
            (PREVIEW / f"Aiko_Current_{name}.png").read_bytes()
            for name in STILLS
        ]
        self.assertEqual(len(payloads), len(set(payloads)))


if __name__ == "__main__":
    unittest.main()
