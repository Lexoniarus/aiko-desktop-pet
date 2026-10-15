"""Rebuilding the approved source preserves calibrated runtime metadata."""

import json
import tempfile
import unittest
from pathlib import Path
from shutil import copy2

try:
    from PIL import Image
except ImportError:
    Image = None

from aiko_pet.asset_paths import ASSET_ROOT


class CharacterPreparationTests(unittest.TestCase):
    @unittest.skipIf(Image is None, "Pillow is needed only for preparation tests")
    def test_rebuild_retains_grip_calibration_without_modifying_imported_source(self):
        from tools.prepare_character_assets import SOURCE, prepare

        source_files = {path: path.read_bytes() for path in SOURCE.rglob("*.json")}
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)
            copy2(ASSET_ROOT / "animation_timing.json", destination)
            prepare(destination=destination)
            first = {path.relative_to(destination): path.read_bytes()
                     for path in destination.rglob("*") if path.is_file()}
            for relative, content in first.items():
                self.assertEqual(content, (ASSET_ROOT / relative).read_bytes(),
                                 relative)
            prepare(destination=destination)
            second = {path.relative_to(destination): path.read_bytes()
                      for path in destination.rglob("*") if path.is_file()}
            self.assertEqual(first, second)
            data = json.loads((destination / "animations.json").read_text("utf-8"))
            eat = next(clip for clip in data["animations"] if clip["state"] == "eat")
            self.assertEqual([frame["food_anchor"][1] for frame in eat["frames"]],
                             [156, 138, 132, 138, 138, 138, 156, 156])
        self.assertEqual(source_files, {path: path.read_bytes()
                                        for path in source_files})
