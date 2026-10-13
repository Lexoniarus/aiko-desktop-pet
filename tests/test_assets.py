"""Check the shipped PNG contract without third-party packages."""

import json
import struct
import unittest
from pathlib import Path

from aiko_pet.presentation.animation import FRAME_COUNTS
from aiko_pet.ui.desktop_window import FRAME_HEIGHT, FRAME_WIDTH


class AssetContractTests(unittest.TestCase):
    def test_every_expected_frame_exists_and_is_correctly_sized(self):
        root = Path(__file__).resolve().parents[1] / "aiko_pet" / "assets"
        manifest = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["frame_counts"], FRAME_COUNTS)
        found = []
        for name, count in FRAME_COUNTS.items():
            for number in range(count):
                file = root / "frames" / name / f"{number:02d}.png"
                self.assertTrue(file.is_file(), str(file))
                data = file.read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                w, h = struct.unpack(">II", data[16:24])
                self.assertEqual((w, h), (FRAME_WIDTH, FRAME_HEIGHT))
                found.append(file)
        self.assertEqual(len(found), 73)
        self.assertEqual(len(list((root / "frames").rglob("*.png"))), 73)


if __name__ == "__main__":
    unittest.main()
