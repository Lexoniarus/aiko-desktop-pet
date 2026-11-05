"""Packaged VN artwork and owner-thread caching, without a Tk interpreter."""

import unittest
from unittest.mock import Mock, patch

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.ui.common.icon_images import IconImages
from aiko_pet.ui.view_models.emotional_text import MOODLET_ICONS


class VnAssetTests(unittest.TestCase):
    def test_runtime_icons_have_complete_mapping_and_loadable_transparent_art(self):
        catalog = load_json(ASSET_ROOT / "ui/catalog.json")
        aliases = {
            "cursor_curiosity": "moodlet_enthusiastic",
            "cursor_fear": "moodlet_uncertain",
        }
        self.assertEqual({k: MOODLET_ICONS[k] for k in aliases}, aliases)
        original = {k: v for k, v in MOODLET_ICONS.items() if k not in aliases}
        self.assertEqual(len(set(original.values())), len(original))
        self.assertLessEqual(set(MOODLET_ICONS.values()), set(catalog["icons"]))
        for sizes in catalog["icons"].values():
            for size, filename in sizes.items():
                with Image.open(ASSET_ROOT / "ui" / filename) as image:
                    self.assertEqual(image.size, (int(size), int(size)))
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(image.getchannel("A").getpixel((0, 0)), 0)
        for filename in catalog["surfaces"].values():
            self.assertTrue((ASSET_ROOT / "ui" / filename).is_file())

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
