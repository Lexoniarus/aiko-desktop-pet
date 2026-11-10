"""Neck installation preserves all artwork, controls and timing outside scope."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from tools.character_export_common import sha256_digest
from tools.character_neck_join_export import expected_paths, export_neck_joins


class NeckJoinExportTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.assets, self.package = self.root / "assets", self.root / "package"
        self.package.mkdir()
        image = Image.new("RGBA", (384, 416))
        image.putpixel((190, 235), (240, 180, 150, 255))
        original = self.encode(image)
        image.putpixel((190, 240), (240, 180, 150, 255))
        candidate = self.encode(image)
        self.changed = {"frames_2x/look/08.png": "front",
                        "body_poses/body-step-right-05/00.png": "walk-right"}
        rows = []
        hd_frames = []
        for relative in sorted(expected_paths()):
            target = self.assets / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
            changed = relative in self.changed
            source = self.package / "frames" / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(candidate if changed else original)
            rows.append({
                "file": relative, "group": self.changed.get(relative, "control"),
                "before_sha256": sha256_digest(original),
                "after_sha256": sha256_digest(candidate if changed else original),
                "after": str(source), "changed_pixels": int(changed),
                "head_translation": [0, 0], "head_scale": 1,
            })
            if relative.startswith("frames_2x/"):
                hd_frames.append({"path": relative.removeprefix("frames_2x/"),
                                  "sha256": sha256_digest(original),
                                  "source": "approved-source"})
        self.inputs: dict[str, Any] = {
            "frames": rows, "reviewed_frames": len(rows),
            "image_generation_calls": 0, "changed_preview_frames": 2,
        }
        self.write_inputs()
        (self.assets / "frames_2x/manifest.json").write_text(json.dumps({
            "version": 1, "size": [384, 416], "frames": hd_frames,
            "neutral_idle_reference": {"keep": True},
        }), "utf-8")
        self.body = {"version": 2, "size": [384, 416],
                     "clips": {"keep": ["unchanged"]},
                     "sources": [{"sha256": "unchanged-native-module"}],
                     "locomotion": {"keep": {"timings": [60, 110]}}}
        (self.assets / "body_poses/manifest.json").write_text(
            json.dumps(self.body), "utf-8",
        )
        self.before = self.snapshot()

    @staticmethod
    def encode(image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def write_inputs(self) -> None:
        (self.package / "vorschau-manifest.json").write_text(
            json.dumps(self.inputs), "utf-8",
        )

    def snapshot(self) -> dict[str, bytes]:
        return {p.relative_to(self.assets).as_posix(): p.read_bytes()
                for p in self.assets.rglob("*") if p.is_file()}

    def test_install_changes_only_reviewed_images_and_metadata_and_is_idempotent(
        self,
    ) -> None:
        self.assertEqual(export_neck_joins(self.package, self.assets),
                         {"corrected_frames": 2, "hd_frames": 1, "body_frames": 1})
        allowed = {*self.changed, "frames_2x/manifest.json"}
        for relative, payload in self.before.items():
            if relative not in allowed:
                self.assertEqual((self.assets / relative).read_bytes(), payload)
        body = json.loads((self.assets / "body_poses/manifest.json").read_text())
        for key, value in self.body.items():
            self.assertEqual(body[key], value)
        after = self.snapshot()
        export_neck_joins(self.package, self.assets)
        self.assertEqual(self.snapshot(), after)

    def test_changed_control_aborts_before_any_install(self) -> None:
        path = self.assets / "frames_2x/idle/07.png"
        path.write_bytes(b"new parallel artwork")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "changed since review"):
            export_neck_joins(self.package, self.assets)
        self.assertEqual(self.snapshot(), before)

    def test_revision_keeps_provenance_for_unchanged_corrected_poses(self) -> None:
        export_neck_joins(self.package, self.assets)
        image_bytes = {p: (self.assets / p).read_bytes() for p in self.changed}
        for row in self.inputs["frames"]:
            row["before_sha256"] = row["after_sha256"]
            row["changed_pixels"] = 0
        self.inputs.update(changed_preview_frames=0, neck_owner="head")
        self.write_inputs()
        self.assertEqual(export_neck_joins(self.package, self.assets),
                         {"corrected_frames": 0, "hd_frames": 1, "body_frames": 1})
        manifest = json.loads((self.assets / "frames_2x/manifest.json").read_text())
        retained = manifest["neck_join_corrections"]["frames"]
        self.assertEqual({r["file"] for r in retained}, set(self.changed))
        for relative, payload in image_bytes.items():
            self.assertEqual((self.assets / relative).read_bytes(), payload)

    def test_matching_source_hash_cannot_authorize_a_change_outside_neck(self) -> None:
        row = next(r for r in self.inputs["frames"] if r["file"] in self.changed)
        source = Path(row["after"])
        with Image.open(source) as image:
            image.putpixel((190, 150), (255, 0, 0, 255))
            image.save(source)
        row["after_sha256"] = sha256_digest(source.read_bytes())
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "protected art"):
            export_neck_joins(self.package, self.assets)
        self.assertEqual(self.snapshot(), self.before)

    def test_missing_source_cannot_partially_install_other_pose(self) -> None:
        row = next(r for r in self.inputs["frames"]
                   if r["file"] == "frames_2x/look/08.png")
        Path(row["after"]).unlink()
        with self.assertRaises(FileNotFoundError):
            export_neck_joins(self.package, self.assets)
        self.assertEqual(self.snapshot(), self.before)

    def test_incomplete_inspected_family_is_rejected(self) -> None:
        self.inputs["frames"].pop()
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "complete reviewed"):
            export_neck_joins(self.package, self.assets)
        self.assertEqual(self.snapshot(), self.before)

    def test_step_collar_metadata_cannot_authorize_a_changed_jaw(self) -> None:
        row = next(r for r in self.inputs["frames"] if r["group"] == "walk-right")
        row["walk_collar_fit"] = {"jaw_boundary_y": 241}
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "approved jaw"):
            export_neck_joins(self.package, self.assets)
        self.assertEqual(self.snapshot(), self.before)

    def test_step_collar_provenance_survives_reinstall(self) -> None:
        row = next(r for r in self.inputs["frames"] if r["group"] == "walk-right")
        row["walk_collar_fit"] = {"jaw_boundary_y": 240}
        self.write_inputs()
        export_neck_joins(self.package, self.assets)
        after = self.snapshot()
        export_neck_joins(self.package, self.assets)
        self.assertEqual(self.snapshot(), after)
        manifest = json.loads((self.assets / "frames_2x/manifest.json").read_text())
        record = next(r for r in manifest["neck_join_corrections"]["frames"]
                      if r["file"] == row["file"])
        self.assertEqual(record["method"], "native_neck_fitted_to_step_collar")
        self.assertEqual(record["walk_collar_fit"]["jaw_boundary_y"], 240)


class InstalledNeckJoinTests(unittest.TestCase):
    def test_installed_join_hashes_and_scope_match_manifest(self) -> None:
        manifest: dict[str, Any] = json.loads(
            (ASSET_ROOT / "frames_2x/manifest.json").read_text("utf-8"),
        )
        rows = manifest["neck_join_corrections"]["frames"]
        expected = {
            f"body_poses/body-look-{side}/{index:02}.png"
            for side in ("left", "right") for index in range(9)
        }
        for side, axes in (("right", range(2, 7)), ("left", range(10, 15))):
            expected.update(
                f"body_poses/body-step-{side}-{axis:02}/{phase}.png"
                for axis in axes for phase in ("stand", "01", "03", "07", "00")
            )
        self.assertEqual({r["file"] for r in rows}, expected)
        self.assertEqual(len(rows), 68)
        # The sixteen frontal joins now belong to the targeted neutral-body
        # replacement; keep their former records as explicitly superseded history.
        frontal = [r for r in manifest["frontal_source_corrections"]["frames"]
                   if r["kind"] == "front_gaze_body_only"]
        self.assertEqual({r["file"] for r in frontal}, {
            f"frames_2x/look/{i:02}.png" for i in range(16)
        })
        self.assertTrue(all(r["previous_neck_join"]["file"] == r["file"]
                            for r in frontal))
        self.assertEqual(manifest["neck_join_corrections"]["neck_owner"], "head")
        for row in rows:
            with self.subTest(file=row["file"]):
                digest = sha256_digest((ASSET_ROOT / row["file"]).read_bytes())
                self.assertEqual(digest, row["sha256"])
                self.assertEqual(row["bounds_2x"], [165, 233, 231, 259])
                self.assertEqual(row["head_translation"], [0, 0])
                self.assertEqual(row["head_scale"], 1)
