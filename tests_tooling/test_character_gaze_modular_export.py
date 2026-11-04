"""Reviewed modular gaze packages preserve body pixels and unrelated assets."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.character_gaze_modular_export import STATUS, export_modular_gaze


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ModularGazeExportTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.hd, self.package = self.root / "frames_2x", self.root / "package"
        for directory in [self.hd / "idle", self.hd / "eat", self.hd / "look",
                          self.package / "look", self.package / "heads"]:
            directory.mkdir(parents=True)
        idle = Image.new("RGBA", (384, 416))
        drawing = ImageDraw.Draw(idle)
        drawing.rectangle((103, 76, 279, 240), fill="white")
        drawing.rectangle((140, 240, 240, 350), fill="blue")
        drawing.rectangle((156, 350, 184, 387), fill="white")
        drawing.rectangle((196, 350, 225, 387), fill="white")
        idle.save(self.hd / "idle/00.png")
        idle.save(self.hd / "eat/00.png")
        self.native = self.root / "frames/idle/00.png"
        self.native.parent.mkdir(parents=True)
        Image.new("RGBA", (192, 208)).save(self.native)
        body = idle.copy()
        body.paste((0, 0, 0, 0), (0, 0, 384, 260))
        body.save(self.package / "body.png")
        self.inputs: dict[str, object] = {
            "version": 1, "size": [384, 416],
            "reference_sha256": digest(self.hd / "idle/00.png"),
            "body_sha256": digest(self.package / "body.png"),
            "shared_body_from_y": 260,
        }
        inputs = []
        self.other_records: list[dict[str, object]] = [
            {"path": "idle/00.png", "status": "idle"},
            {"path": "eat/00.png", "status": "accepted-eating"},
        ]
        records = self.other_records.copy()
        for index in range(16):
            relative = f"look/{index:02}.png"
            image = idle.copy()
            image.putpixel((150 + index, 100), (10, 100, 200, 255))
            if index == 15:
                image.putpixel((110, 100), (10, 100, 200, 96))
            image.save(self.package / relative)
            image.save(self.package / f"heads/{index:02}.png")
            idle.save(self.hd / relative)
            inputs.append({
                "path": relative, "sha256": digest(self.package / relative),
                "head_sha256": digest(self.package / f"heads/{index:02}.png"),
                "head_provenance": {"source": f"private-heads/{index:02}.png",
                                    "size": [1254, 1254]},
            })
            records.append({"path": relative, "old": True})
        self.inputs["frames"] = inputs
        self.write_inputs()
        (self.hd / "manifest.json").write_text(json.dumps({
            "version": 1, "size": [384, 416], "frames": records,
        }), "utf-8")
        self.before = {p: p.read_bytes() for p in self.root.rglob("*")
                       if p.is_file() and not p.is_relative_to(self.package)}

    def write_inputs(self) -> None:
        (self.package / "manifest.json").write_text(json.dumps(self.inputs), "utf-8")

    def assert_live_unchanged(self) -> None:
        for path, content in self.before.items():
            self.assertEqual(path.read_bytes(), content, str(path))

    def test_complete_import_keeps_native_eating_and_reviewed_body(self) -> None:
        records = export_modular_gaze(self.package, self.hd)
        self.assertEqual(len(records), 16)
        manifest = json.loads((self.hd / "manifest.json").read_text("utf-8"))
        self.assertEqual(manifest["frames"][:2], self.other_records)
        for path in [self.native, self.hd / "idle/00.png", self.hd / "eat/00.png"]:
            self.assertEqual(path.read_bytes(), self.before[path])
        with Image.open(self.hd / "idle/00.png") as idle:
            lower = idle.crop((0, 260, 384, 416)).tobytes()
        for index, record in enumerate(records):
            self.assertEqual(record["status"], STATUS)
            self.assertEqual(record["degrees_clockwise_from_up"], index * 22.5)
            self.assertEqual(record["alpha128_normalized_pixels"], int(index == 15))
            path = self.hd / f"look/{index:02}.png"
            self.assertEqual(digest(path), record["sha256"])
            with Image.open(path) as image:
                self.assertEqual(image.crop((0, 260, 384, 416)).tobytes(), lower)
                self.assertEqual(set(image.getchannel("A").tobytes()), {0, 255})
                self.assertEqual(image.getpixel((150 + index, 100)),
                                 (10, 100, 200, 255))
            if index != 15:
                self.assertEqual(path.read_bytes(),
                                 (self.package / f"look/{index:02}.png").read_bytes())

    def test_missing_final_head_never_replaces_earlier_live_frames(self) -> None:
        (self.package / "heads/15.png").unlink()
        with self.assertRaises(FileNotFoundError):
            export_modular_gaze(self.package, self.hd)
        self.assert_live_unchanged()

    def test_unreviewed_frame_digest_is_rejected_before_live_changes(self) -> None:
        path = self.package / "look/15.png"
        with Image.open(path) as image:
            image.putpixel((190, 300), (1, 2, 3, 255))
            image.save(path)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            export_modular_gaze(self.package, self.hd)
        self.assert_live_unchanged()

    def test_even_a_matching_digest_cannot_import_a_changed_body(self) -> None:
        path = self.package / "look/15.png"
        with Image.open(path) as image:
            image.putpixel((190, 300), (1, 2, 3, 255))
            image.save(path)
        data = json.loads((self.package / "manifest.json").read_text("utf-8"))
        data["frames"][-1]["sha256"] = digest(path)
        (self.package / "manifest.json").write_text(json.dumps(data), "utf-8")
        with self.assertRaisesRegex(ValueError, "shared lower body"):
            export_modular_gaze(self.package, self.hd)
        self.assert_live_unchanged()

    def test_mismatched_idle_reference_is_rejected_before_live_changes(self) -> None:
        self.inputs["reference_sha256"] = "0" * 64
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "different Idle"):
            export_modular_gaze(self.package, self.hd)
        self.assert_live_unchanged()
