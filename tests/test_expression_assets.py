"""Approved baked sources, strict pack loading and fixed-foot Tk rendering."""

import json
import shutil
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.expression_assets import load_expression_clips
from aiko_pet.ui.pet_view.body_pose_cache import BodyPoseCache
from aiko_pet.ui.pet_view.rest_pose_renderer import RestPoseRenderer


class ExpressionAssetsTests(unittest.TestCase):
    def test_pack_retains_48_phases_neutral_endpoints_and_identical_lower_body(self):
        clips = load_expression_clips(ASSET_ROOT)
        self.assertEqual(len(clips), 6)
        neutral = clips["rest-neutral"].frames[0].file.read_bytes()
        body = None
        for name, clip in clips.items():
            self.assertTrue(clip.rest_sway)
            self.assertEqual(len(clip.frames), 8)
            self.assertEqual(clip.anchor, (96, 194))
            for frame in clip.frames:
                with Image.open(frame.file) as image:
                    self.assertEqual(image.size, (384, 416))
                    self.assertEqual(sum(image.getchannel("A").histogram()[1:255]), 0)
                    lower = image.convert("RGBA").crop((0, 265, 384, 416)).tobytes()
                if body is None:
                    body = lower
                self.assertEqual(lower, body)
            if name != "rest-neutral":
                self.assertEqual(clip.frames[0].file.read_bytes(), neutral)
                self.assertEqual(clip.frames[7].file.read_bytes(), neutral)

    def test_loader_rejects_partial_and_modified_packs_but_allows_absent_pack(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(dict(load_expression_clips(root)), {})
            shutil.copytree(ASSET_ROOT / "expressions", root / "expressions")
            manifest = root / "expressions/manifest.json"
            data = json.loads(manifest.read_text("utf-8"))
            record = data["clips"]["rest-neutral"]["frames"][0]
            source = root / record["file"]
            source.write_bytes(source.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "digest"):
                load_expression_clips(root)
            del data["clips"]["expression-positive"]
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                load_expression_clips(root)

    def test_real_tk_scaled_frames_and_sway_preserve_the_stationary_feet(self):
        root = tk.Tk()
        root.withdraw()
        catalog = load_character_catalog()
        cache = BodyPoseCache(root, catalog)
        renderer = RestPoseRenderer(root)
        try:
            with tempfile.TemporaryDirectory() as folder:
                for scale in (1, 2):
                    views = cache.for_scale(scale)
                    for name in catalog.expression_clips:
                        image = views[name][3]
                        self.assertEqual((image.width(), image.height()),
                                         (192 * scale, 208 * scale))
                        paths = [Path(folder) / "original.png",
                                 Path(folder) / "sway.png"]
                        image.write(str(paths[0]), format="png")
                        warped = renderer.resolve(image, offset=1, scale=scale)
                        warped.write(str(paths[1]), format="png")
                        with (Image.open(paths[0]) as left,
                              Image.open(paths[1]) as right):
                            for rendered in (left, right):
                                self.assertEqual(sum(
                                    rendered.getchannel("A").histogram()[1:255],
                                ), 0)
                            area = (0, 174 * scale, 192 * scale, 208 * scale)
                            self.assertEqual(left.convert("RGBA").crop(area).tobytes(),
                                             right.convert("RGBA").crop(area).tobytes())
                            self.assertNotEqual(left.tobytes(), right.tobytes())
        finally:
            renderer.clear()
            cache.close()
            root.destroy()
