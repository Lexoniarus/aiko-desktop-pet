"""Packaged VN artwork and owner-thread caching, without a Tk interpreter."""

import hashlib
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.ui.common.icon_images import IconImages
from aiko_pet.ui.view_models.emotional_text import MOODLET_ICONS
from tools.export_vn_ui import nine_slice


class VnAssetTests(unittest.TestCase):
    def test_exports_cover_selected_masters_and_keep_original_hashes(self):
        catalog = load_json(ASSET_ROOT / "ui/catalog.json")
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(len(catalog["icons"]), 54)
        self.assertEqual(len(catalog["source_sha256"]), 62)
        self.assertEqual(len(set(MOODLET_ICONS.values())), len(MOODLET_ICONS))
        self.assertLessEqual(set(MOODLET_ICONS.values()), set(catalog["icons"]))
        for path, expected in catalog["source_sha256"].items():
            self.assertEqual(
                hashlib.sha256((root / path).read_bytes()).hexdigest(), expected, path
            )
        for sizes in catalog["icons"].values():
            for size, filename in sizes.items():
                with Image.open(ASSET_ROOT / "ui" / filename) as image:
                    self.assertEqual(image.size, (int(size), int(size)))
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(image.getchannel("A").getpixel((0, 0)), 0)
        for filename in catalog["surfaces"].values():
            self.assertTrue((ASSET_ROOT / "ui" / filename).is_file())

    def test_nine_slice_preserves_caps_and_transparent_center(self):
        source = Image.new("RGBA", (80, 20))
        source.putpixel((0, 0), (255, 0, 0, 255))
        output = nine_slice(source, (160, 20))
        self.assertEqual(output.getpixel((0, 0)), (255, 0, 0, 255))
        self.assertEqual(output.getchannel("A").getpixel((80, 10)), 0)

    def test_cache_is_root_local_reuses_images_and_releases_without_windows(self):
        root = Mock()
        with patch("aiko_pet.ui.common.icon_images.tk.PhotoImage") as photo:
            owner = IconImages(root)
            first = owner.icon("status_fun")
            self.assertIs(owner.icon("status_fun"), first)
            photo.assert_called_once()
            owner.release()
            self.assertFalse(owner._images)
            with self.assertRaises(RuntimeError):
                owner.icon("status_fun")
