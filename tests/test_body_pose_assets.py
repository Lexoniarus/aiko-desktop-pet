"""The independent body pack preserves the normal atlas and loads both sizes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.body_pose_assets import load_body_pose_clips
from aiko_pet.infrastructure.character_assets import load_character_catalog


class BodyPoseAssetTests(unittest.TestCase):
    def test_step_clips_share_timing_and_family_across_head_axes(self) -> None:
        clips = load_character_catalog().body_clips
        for side in ("left", "right"):
            variants = [c for c in clips.values() if c.family == f"body-step-{side}"]
            self.assertEqual(len(variants), 6)
            self.assertTrue(all(c.timings == variants[0].timings for c in variants))
            self.assertTrue(all(c.stride == 16 for c in variants))
            self.assertTrue(all(c.movement and c.loop for c in variants))

    def test_installed_pack_keeps_normal_catalog_independent(self) -> None:
        catalog = load_character_catalog()
        self.assertEqual(len(catalog.clips), 16)
        self.assertEqual(len(catalog.body_clips), 18)
        for name, clip in catalog.body_clips.items():
            self.assertEqual(
                len(clip.frames), 6 if clip.movement else 5 if "turn" in name else 9,
            )
            for frame in clip.frames:
                with Image.open(frame.file) as image:
                    self.assertEqual(image.size, (384, 416))
                    self.assertEqual(image.mode, "RGBA")
                    self.assertLessEqual(set(image.getchannel("A").tobytes()), {0, 255})

    def test_old_install_without_pack_has_no_orientation_clips(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(load_body_pose_clips(Path(folder)))

    def test_pack_rejects_path_escaping_asset_root(self) -> None:
        data = json.loads((ASSET_ROOT / "body_poses/manifest.json").read_text("utf-8"))
        data["clips"]["body-turn-left"][0] = "../../outside.png"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "body_poses").mkdir()
            (root / "body_poses/manifest.json").write_text(json.dumps(data), "utf-8")
            with self.assertRaisesRegex(ValueError, "escapes"):
                load_body_pose_clips(root)
