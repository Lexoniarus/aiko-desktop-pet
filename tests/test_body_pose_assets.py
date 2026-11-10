"""The independent body pack preserves the normal atlas and loads both sizes."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.body_pose_assets import load_body_pose_clips
from aiko_pet.infrastructure.character_assets import load_character_catalog


class BodyPoseAssetTests(unittest.TestCase):
    def test_frontal_gazes_keep_v3_heads_on_current_neutral_body(self) -> None:
        data = json.loads((ASSET_ROOT / "frames_2x/manifest.json").read_text("utf-8"))
        provenance = data["frontal_source_corrections"]
        reference = ASSET_ROOT / provenance["reference"]
        self.assertEqual(hashlib.sha256(reference.read_bytes()).hexdigest(),
                         provenance["reference_sha256"])
        with Image.open(reference) as image:
            lower = image.convert("RGBA").crop((0, 260, 384, 416)).tobytes()
        rows = [r for r in provenance["frames"] if r["kind"] == "front_gaze_body_only"]
        self.assertEqual({r["file"] for r in rows},
                         {f"frames_2x/look/{i:02}.png" for i in range(16)})
        for row in rows:
            with (
                self.subTest(frame=row["file"]),
                Image.open(ASSET_ROOT / row["file"]) as im,
            ):
                image = im.convert("RGBA")
                self.assertEqual(image.crop((0, 260, 384, 416)).tobytes(), lower)
                head = image.crop((0, 0, 384, row["head_before_y"])).tobytes()
                self.assertEqual(
                    hashlib.sha256(head).hexdigest(), row["head_pixels_sha256"],
                )

    def test_first_turn_step_reuses_neutral_v3_upper_and_retains_legs(self) -> None:
        path = ASSET_ROOT / "body_poses/frontal-source-2026-11-06.json"
        data = json.loads(path.read_text("utf-8"))
        self.assertEqual(len(data["frames"]), 4)
        with Image.open(ASSET_ROOT / data["reference"]) as im:
            neutral = im.convert("RGBA")
        for row in data["frames"]:
            with (
                self.subTest(frame=row["file"]),
                Image.open(ASSET_ROOT / row["file"]) as im,
            ):
                registered = Image.new("RGBA", (384, 416))
                registered.paste(neutral, tuple(row["translation"]))
                self.assertEqual(im.crop((0, 0, 384, 283)).tobytes(),
                                 registered.crop((0, 0, 384, 283)).tobytes())
                lower = im.crop((0, row["protected_lower_from_y"], 384, 416)).tobytes()
                self.assertEqual(
                    hashlib.sha256(lower).hexdigest(), row["protected_lower_sha256"],
                )

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
