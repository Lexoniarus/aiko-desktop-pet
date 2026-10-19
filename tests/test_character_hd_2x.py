"""Validate the new HD character assets without altering the 1x sources."""

from __future__ import annotations

import hashlib
import json
import tkinter as tk
import unittest

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.ui.pet_view.character_sprite_cache import CharacterSpriteCache

try:
    from PIL import Image
except ImportError:
    Image = None

HD_ROOT = ASSET_ROOT / "frames_2x"


class HighResolutionCharacterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads((HD_ROOT / "manifest.json").read_text("utf-8"))

    def test_manifest_covers_every_unique_current_character_frame(self) -> None:
        catalog = load_character_catalog()
        expected = {
            frame.file.relative_to(ASSET_ROOT / "frames").as_posix()
            for clip in catalog.clips.values() for frame in clip.frames
        }
        self.assertEqual(len(expected), 120)
        self.assertEqual(self.metadata["version"], 1)
        self.assertEqual(self.metadata["size"], [384, 416])
        images = self.metadata["frames"]
        self.assertEqual(len(images), 120)
        self.assertEqual({entry["path"] for entry in images}, expected)
        self.assertEqual(len({entry["path"] for entry in images}), 120)
        statuses = {entry["status"] for entry in images}
        self.assertNotIn("fallback_from_native_1x_corrupt_source", statuses)

    def test_each_asset_has_the_expected_digest_and_size(self) -> None:
        for item in self.metadata["frames"]:
            with self.subTest(asset=item["path"]):
                path = HD_ROOT / item["path"]
                self.assertTrue(path.is_file())
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest, item["sha256"])

    @unittest.skipIf(Image is None, "Pillow required for visual asset verification")
    def test_2x_images_are_384_by_416_rgba_with_binary_transparency(self) -> None:
        assert Image is not None
        for item in self.metadata["frames"]:
            with self.subTest(asset=item["path"]):
                with Image.open(HD_ROOT / item["path"]) as source:
                    self.assertEqual(source.size, (384, 416))
                    self.assertEqual(source.mode, "RGBA")
                    alpha = source.getchannel("A")
                    self.assertEqual(alpha.getextrema(), (0, 255))
                    values = set(alpha.getdata())
                    self.assertEqual(values, {0, 255})

    def test_app_retains_exact_original_native_frame_catalogue(self) -> None:
        manifest = json.loads((ASSET_ROOT / "provenance.json").read_text("utf-8"))
        for rel, sha in manifest["runtime_sha256"].items():
            digest = hashlib.sha256((ASSET_ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(digest, sha)


class TrueHDSpriteCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            probe = tk.Tk()
        except tk.TclError as e:
            raise unittest.SkipTest("Desktop display required") from e
        probe.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.cache = CharacterSpriteCache(self.root, load_character_catalog())
        self.addCleanup(self.cache.close)

    def test_loads_native_and_real_hd_images_lazily_and_reuses_them(self) -> None:
        native = self.cache.for_scale(1)["idle"][0]
        hd_view = self.cache.for_scale(2)["idle"]
        self.assertEqual(native.width(), 192)
        self.assertEqual(native.height(), 208)
        self.assertEqual(len(getattr(hd_view, "_zoomed")), 0)
        high = hd_view[0]
        self.assertEqual((high.width(), high.height()), (384, 416))
        self.assertIs(high, hd_view[0])
        self.assertEqual(len(getattr(hd_view, "_zoomed")), 1)
        # A true 2x image must be different from a nearest-neighbor zoom.
        legacy = native.zoom(2)
        sampled = [
            (x, y) for x in range(80, 275, 7) for y in range(95, 395, 7)
        ]
        self.assertTrue(any(
            high.get(x, y) != legacy.get(x, y) for x, y in sampled
        ))
        native_again = self.cache.for_scale(1)["idle"][0]
        self.assertEqual((native_again.width(), native_again.height()),
                         (192, 208))

    def test_all_look_and_pickup_frames_are_available_at_true_2x(self) -> None:
        for state, frames in (("look", 16), ("pick_up", 8)):
            images = self.cache.for_scale(2)[state]
            self.assertEqual(len(images), frames)
            for idx in (0, frames - 1):
                self.assertEqual(
                    (images[idx].width(), images[idx].height()), (384, 416),
                )


if __name__ == "__main__":
    unittest.main()
