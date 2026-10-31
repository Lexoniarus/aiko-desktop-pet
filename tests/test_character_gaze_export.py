"""Gaze extraction and foot registration regressions without owner archives."""

from __future__ import annotations

import hashlib
import json
import unittest

from PIL import Image, ImageDraw

from aiko_pet.asset_paths import ASSET_ROOT
from tools.character_export_common import planted_foot_bounds
from tools.character_gaze_export import (
    extract_gaze_poses,
    register_gaze_row,
)


class GazeRegistrationTests(unittest.TestCase):
    @staticmethod
    def source() -> Image.Image:
        strip = Image.new("RGBA", (310, 140))
        draw = ImageDraw.Draw(strip)
        # Near-transparent source noise bridges otherwise separate figures.
        draw.line((0, 12, 309, 12), fill=(255, 255, 255, 1))
        for center, color in zip(
            (75, 170, 270),
            ((255, 0, 0), (0, 255, 0), (0, 0, 255)),
            strict=True,
        ):
            draw.rectangle((center - 32, 10, center + 32, 55), fill=(*color, 255))
            draw.rectangle((center - 12, 50, center + 12, 90), fill=(*color, 255))
            draw.rectangle((center - 10, 85, center - 2, 115), fill=(*color, 255))
            draw.rectangle((center + 2, 85, center + 10, 115), fill=(*color, 255))
        return strip

    @staticmethod
    def references() -> list[Image.Image]:
        images = []
        for center in (90, 96, 102):
            image = Image.new("RGBA", (192, 208))
            draw = ImageDraw.Draw(image)
            draw.rectangle((center - 25, 50, center + 25, 100), fill="white")
            draw.rectangle((center - 9, 95, center + 9, 180), fill="white")
            draw.rectangle((center - 9, 176, center - 1, 193), fill="white")
            draw.rectangle((center + 1, 176, center + 9, 193), fill="white")
            images.append(image)
        return images

    def test_cross_cell_hair_and_alpha_noise_do_not_mix_neighboring_poses(self) -> None:
        poses = extract_gaze_poses(self.source(), 3)
        self.assertEqual(len(poses), 3)
        # First head extends beyond the old equal-width cell boundary.
        self.assertGreater(poses[0].source_crop[2], 310 / 3)
        for pose, color in zip(
            poses,
            ((255, 0, 0), (0, 255, 0), (0, 0, 255)),
            strict=True,
        ):
            rgba = pose.image.tobytes()
            colors = {
                tuple(rgba[offset : offset + 3])
                for offset in range(0, len(rgba), 4)
                if rgba[offset + 3] >= 8
            }
            self.assertEqual(colors, {color})

    def test_common_proportional_scale_keeps_each_foot_anchor(self) -> None:
        results = register_gaze_row(self.source(), self.references())
        self.assertEqual(len({info["row_scale"] for _, info in results}), 1)
        for (image, info), reference in zip(results, self.references(), strict=True):
            self.assertEqual(image.size, (384, 416))
            self.assertLess(abs(info["aspect_rescale_ratio"] - 1), 0.01)
            self.assertLessEqual(abs(info["foot_anchor_error"][0]), 0.5)
            self.assertEqual(info["foot_anchor_error"][1], 0)
            feet = image.getchannel("A").crop((0, 352, 384, 388)).getbbox()
            native_feet = reference.getchannel("A").crop((0, 176, 192, 194)).getbbox()
            assert feet is not None and native_feet is not None
            self.assertLessEqual(
                abs((feet[0] + feet[2]) / 2 - native_feet[0] - native_feet[2]),
                0.5,
            )
            self.assertEqual(feet[3], 36)

    def test_unexpected_pose_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Expected 8 separate gaze poses"):
            extract_gaze_poses(self.source())

    def test_pose_size_adjustments_keep_proportions_and_planted_feet(self) -> None:
        references = self.references()
        base = register_gaze_row(self.source(), references)
        adjusted = register_gaze_row(
            self.source(),
            references,
            scale_adjustments=[1.0, 1.0115, 1.023],
        )
        for (original, _), (image, info) in zip(base, adjusted, strict=True):
            original_bounds = original.getchannel("A").getbbox()
            bounds = image.getchannel("A").getbbox()
            assert original_bounds is not None and bounds is not None
            self.assertGreaterEqual(
                bounds[3] - bounds[1], original_bounds[3] - original_bounds[1]
            )
            self.assertLess(abs(info["aspect_rescale_ratio"] - 1), 0.01)
            feet = image.getchannel("A").crop((0, 352, 384, 388)).getbbox()
            original_feet = original.getchannel("A").crop((0, 352, 384, 388)).getbbox()
            assert feet is not None and original_feet is not None
            self.assertLessEqual(
                abs(sum(feet[::2]) / 2 - sum(original_feet[::2]) / 2),
                0.5,
            )
            self.assertEqual(feet[3], 36)

    def test_invalid_scale_adjustments_are_rejected(self) -> None:
        for adjustments in ([], [1.0, 1.0], [1.0, 0.0, 1.0], [1.0, float("nan"), 1.0]):
            with self.subTest(adjustments=adjustments):
                with self.assertRaisesRegex(ValueError, "positive finite scale"):
                    register_gaze_row(
                        self.source(),
                        self.references(),
                        scale_adjustments=adjustments,
                    )

    def test_horizontal_offsets_translate_pixels_without_resizing(self) -> None:
        references = self.references()
        baseline = register_gaze_row(self.source(), references)
        offsets = [-1, 1, -1]
        shifted = register_gaze_row(
            self.source(),
            references,
            horizontal_offsets=offsets,
        )
        for (before, base_info), (after, info), offset in zip(
            baseline,
            shifted,
            offsets,
            strict=True,
        ):
            expected = Image.new("RGBA", before.size)
            expected.paste(before, (offset, 0))
            self.assertEqual(after.tobytes(), expected.tobytes())
            self.assertEqual(
                info["aspect_rescale_ratio"], base_info["aspect_rescale_ratio"]
            )
            self.assertEqual(
                info["rendered_foot_anchor"][0],
                base_info["rendered_foot_anchor"][0] + offset,
            )
            self.assertEqual(
                info["rendered_foot_anchor"][1], base_info["rendered_foot_anchor"][1]
            )
        with self.assertRaisesRegex(ValueError, "one horizontal offset"):
            register_gaze_row(self.source(), references, horizontal_offsets=[1])


class ShippedGazeExportTests(unittest.TestCase):
    def test_lateral_foot_transitions_are_quiet_around_both_corrected_pairs(
        self,
    ) -> None:
        centers = []
        for index in range(16):
            with Image.open(
                ASSET_ROOT / "frames_2x" / f"look/{index:02d}.png"
            ) as image:
                feet = image.getchannel("A").crop((0, 352, 384, 388)).getbbox()
                assert feet is not None
                centers.append((feet[0] + feet[2]) / 2)
                self.assertEqual(feet[3], 36)
        for first, second in ((10, 11), (14, 15)):
            self.assertLessEqual(abs(centers[first] - centers[second]), 0.5)
        # Include the neighbors and the wrap: smoothing must not move the jump.
        for index in range(16):
            self.assertLessEqual(abs(centers[index] - centers[(index + 1) % 16]), 1.5)

    def test_all_gaze_body_scales_match_idle_while_head_pitch_can_change(
        self,
    ) -> None:
        hd_root = ASSET_ROOT / "frames_2x"
        with Image.open(hd_root / "idle/00.png") as idle:
            reference_feet = planted_foot_bounds(idle)
            reference_body = idle.crop((0, 260, 384, 416)).tobytes()
        manifest = json.loads((hd_root / "manifest.json").read_text("utf-8"))
        entries = {entry["path"]: entry for entry in manifest["frames"]}
        for index in range(16):
            with self.subTest(direction=index):
                with Image.open(hd_root / f"look/{index:02d}.png") as image:
                    feet = planted_foot_bounds(image)
                    self.assertEqual(image.crop((0, 260, 384, 416)).tobytes(),
                                     reference_body)
                self.assertEqual(feet[3], reference_feet[3])
                entry = entries[f"look/{index:02d}.png"]
                self.assertEqual(entry["scale_calibration"],
                                 "shared_idle_body_pixels")
                self.assertEqual(entry["shared_body_from_y"], 260)
                self.assertEqual(entry["body_sha256"],
                                 entries["look/00.png"]["body_sha256"])

    def test_modular_sources_keep_idle_foot_anchors_and_sector_mapping(
        self,
    ) -> None:
        hd_root = ASSET_ROOT / "frames_2x"
        manifest = json.loads((hd_root / "manifest.json").read_text("utf-8"))
        entries = {entry["path"]: entry for entry in manifest["frames"]}
        idle_path = hd_root / "idle/00.png"
        idle_sha = hashlib.sha256(idle_path.read_bytes()).hexdigest()
        with Image.open(idle_path) as idle:
            target = planted_foot_bounds(idle)
        target_x = (target[0] + target[2]) / 2
        for index in range(16):
            path = f"look/{index:02d}.png"
            entry = entries[path]
            self.assertEqual(entry["source"],
                             f"private-v3-gaze-modular/look/{index:02d}.png")
            self.assertEqual(entry["status"], "composited_v3_gaze_shared_idle_body")
            self.assertEqual(entry["source_size"], [384, 416])
            self.assertGreaterEqual(min(entry["head_provenance"]["size"]), 1000)
            self.assertEqual(entry["reference_sha256"], idle_sha)
            self.assertEqual(entry["degrees_clockwise_from_up"], index * 22.5)
            self.assertLess(abs(entry["aspect_rescale_ratio"] - 1), 0.006)
            with Image.open(hd_root / path) as hd:
                feet = planted_foot_bounds(hd)
            self.assertLessEqual(abs((feet[0] + feet[2]) / 2 - target_x), 0.5)
            self.assertEqual(feet[3], target[3])


if __name__ == "__main__":
    unittest.main()
