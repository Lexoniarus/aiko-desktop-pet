"""The neutral Idle export must not recompose approved gaze or side poses."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from tools.character_export_common import sha256_digest
from tools.character_neck_join_export import protected_pixels
from tools.character_neutral_idle_export import export_neutral_idle


class NeutralIdleExportTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.assets = Path(temporary.name) / "assets"
        neutral = []
        records: list[dict[str, Any]] = []
        for i in range(8):
            relative = f"expressions/rest-neutral/{i:02}.png"
            path = self.assets / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", (384, 416), (i, 100, 200, 255)).save(path)
            neutral.append({"file": relative,
                            "sha256": sha256_digest(path.read_bytes())})
            target = self.assets / f"frames_2x/idle/{i:02}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", (384, 416), "white").save(target)
            records.append({"path": f"idle/{i:02}.png", "legacy": True})
        for relative in ("frames_2x/look/06.png", "frames/idle/00.png",
                         "frames_2x/eat/00.png", "body_poses/body-look-right/06.png",
                         "body_poses/body-step-left-10/03.png"):
            path = self.assets / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"approved unrelated image")
        self.other_records = [{"path": "look/06.png", "approved": "gaze"},
                              {"path": "eat/00.png", "approved": "eating"}]
        (self.assets / "body_poses/manifest.json").write_bytes(b"approved body data")
        self.manifest = self.assets / "frames_2x/manifest.json"
        self.manifest.write_text(json.dumps({
            "version": 1, "size": [384, 416],
            "frames": [*records, *self.other_records],
        }), "utf-8")
        (self.assets / "expressions/manifest.json").write_text(json.dumps({
            "version": 1, "size": [384, 416],
            "clips": {"rest-neutral": {"frames": neutral}},
        }), "utf-8")

    def snapshot(self) -> dict[str, bytes]:
        return {p.relative_to(self.assets).as_posix(): p.read_bytes()
                for p in self.assets.rglob("*") if p.is_file()}

    def test_only_idle_is_replaced_and_repeated_export_is_idempotent(self) -> None:
        before = self.snapshot()
        manifest = export_neutral_idle(self.assets)
        for relative, payload in before.items():
            if relative == "frames_2x/manifest.json":
                continue
            if relative.startswith("frames_2x/idle/"):
                approved = relative.replace("frames_2x/idle/",
                                            "expressions/rest-neutral/")
                payload = before[approved]
            self.assertEqual((self.assets / relative).read_bytes(), payload, relative)
        self.assertEqual(manifest["frames"][8:], self.other_records)
        after = self.snapshot()
        export_neutral_idle(self.assets)
        self.assertEqual(self.snapshot(), after)

    def test_invalid_final_neutral_phase_cannot_partially_write(self) -> None:
        path = self.assets / "expressions/rest-neutral/07.png"
        path.write_bytes(b"wrong source")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            export_neutral_idle(self.assets)
        self.assertEqual(self.snapshot(), before)

    def test_broad_rebase_requires_restoration_before_idle_export(self) -> None:
        manifest = json.loads(self.manifest.read_text("utf-8"))
        manifest["frontal_reference"] = {"gaze_head_transform": "wrong scope"}
        self.manifest.write_text(json.dumps(manifest), "utf-8")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Restore approved gaze/body"):
            export_neutral_idle(self.assets)
        self.assertEqual(self.snapshot(), before)


class InstalledNeutralIdleTests(unittest.TestCase):
    def test_approved_gaze_and_body_art_outside_neck_matches_snapshot(self) -> None:
        # Pin the approved 06.11 scope: sixteen frontal bodies, four turn
        # starts and ten true-profile joins. Other accepted art stays fixed.
        expected = {
            "frames_2x/look": (
                16, "9bf2483fda696b7ac2c41506c07e606f4a14714b2e8396d13c7662e15d6eb89f",
            ),
            "body_poses": (
                102, "9f7bf07b1952d0744b6e12945cc45e40720e8866f88ee82cef17562c7cae9d15",
            ),
        }
        for folder, (count, digest) in expected.items():
            paths = sorted((ASSET_ROOT / folder).rglob("*.png"))
            rows = []
            for path in paths:
                with Image.open(path) as image:
                    pixels = protected_pixels(image.convert("RGBA"))
                rows.append(path.relative_to(ASSET_ROOT).as_posix() + ":"
                            + hashlib.sha256(pixels).hexdigest())
            self.assertEqual(len(paths), count)
            self.assertEqual(
                hashlib.sha256("\n".join(rows).encode()).hexdigest(), digest,
            )

    def test_hd_idle_preserves_exact_approved_neutral_phases(self) -> None:
        for i in range(8):
            self.assertEqual(
                (ASSET_ROOT / f"frames_2x/idle/{i:02}.png").read_bytes(),
                (ASSET_ROOT / f"expressions/rest-neutral/{i:02}.png").read_bytes(),
            )

    def test_turns_keep_the_original_idle_endpoint(self) -> None:
        manifest = json.loads((ASSET_ROOT / "body_poses/manifest.json").read_text())
        for name in ("body-turn-left", "body-turn-right",
                     "body-orient-left", "body-orient-right"):
            self.assertEqual(manifest["clips"][name][0], "frames_2x/idle/00.png")
