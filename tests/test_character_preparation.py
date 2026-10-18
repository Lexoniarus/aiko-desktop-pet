"""Rebuilding the approved source preserves calibrated runtime metadata."""

import hashlib
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
        assert Image is not None
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)
            copy2(ASSET_ROOT / "animation_timing.json", destination)
            prepare(destination=destination)
            first = {path.relative_to(destination): path.read_bytes()
                     for path in destination.rglob("*") if path.is_file()}
            for relative, content in first.items():
                shipped = ASSET_ROOT / relative
                if relative.suffix == ".png":
                    with Image.open(destination / relative) as generated:
                        with Image.open(shipped) as approved:
                            self.assertEqual(generated.size, approved.size, relative)
                            self.assertEqual(generated.convert("RGBA").tobytes(),
                                             approved.convert("RGBA").tobytes(),
                                             relative)
                elif relative == Path("provenance.json"):
                    generated_manifest = json.loads(content)
                    shipped_manifest = json.loads(shipped.read_bytes())
                    generated_hashes = generated_manifest.pop("runtime_sha256")
                    shipped_hashes = shipped_manifest.pop("runtime_sha256")
                    self.assertEqual(generated_manifest, shipped_manifest)
                    self.assertEqual(generated_hashes.keys(), shipped_hashes.keys())
                    for root, hashes in ((destination, generated_hashes),
                                         (ASSET_ROOT, shipped_hashes)):
                        for file, digest in hashes.items():
                            self.assertEqual(
                                hashlib.sha256((root / file).read_bytes()).hexdigest(),
                                digest, file,
                            )
                else:
                    self.assertEqual(content, shipped.read_bytes(), relative)
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
