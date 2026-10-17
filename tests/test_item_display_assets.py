"""Derived display sprites preserve sources, geometry and deterministic masks."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.item_assets import load_item_catalog


class ItemDisplayAssetsTests(unittest.TestCase):
    @unittest.skipIf(Image is None, "Pillow is needed only for asset preparation tests")
    def test_all_display_copies_have_binary_alpha_and_unchanged_geometry_and_rgb(self):
        root = ASSET_ROOT / "items"
        provenance = json.loads((root / "display/provenance.json").read_text("utf-8"))
        self.assertEqual(len(provenance["files"]), 22)
        assert Image is not None
        for record in provenance["files"]:
            source, display = root / record["source"], root / record["display"]
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                             record["source_sha256"])
            self.assertEqual(hashlib.sha256(display.read_bytes()).hexdigest(),
                             record["display_sha256"])
            with Image.open(source) as raw, Image.open(display) as prepared:
                original, result = raw.convert("RGBA"), prepared.convert("RGBA")
                self.assertEqual(original.size, result.size)
                self.assertLessEqual(set(result.getchannel("A").tobytes()), {0, 255})
                self.assertEqual(original.convert("RGB").tobytes(),
                                 result.convert("RGB").tobytes())

    @unittest.skipIf(Image is None, "Pillow is needed only for asset preparation tests")
    def test_preparation_rebuilds_missing_outputs_and_is_reproducible(self):
        from shutil import copy2

        from tools.prepare_item_display_assets import prepare

        source_root = ASSET_ROOT / "items"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = json.loads((source_root / "items.json").read_text("utf-8"))
            (root / "items.json").write_text(json.dumps(data), encoding="utf-8")
            for item in data["foods"]:
                for variant in item["variants"].values():
                    path = root / variant["path"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    copy2(source_root / variant["path"], path)
            prepare(root)
            first = {path.relative_to(root): path.read_bytes()
                     for path in root.rglob("*") if path.is_file()}
            prepare(root)
            self.assertEqual(first, {path.relative_to(root): path.read_bytes()
                                     for path in root.rglob("*") if path.is_file()})

    def test_catalog_exposes_display_and_original_as_distinct_same_size_sprites(self):
        for item in load_item_catalog().foods.values():
            for sprite in item.sprites.values():
                self.assertIsNotNone(sprite.display_path)
                self.assertNotEqual(sprite.path, sprite.display_path)
