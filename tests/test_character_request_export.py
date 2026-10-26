"""Full request-gesture imports preserve references and reject unsafe packages."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.character_export_common import sha256_digest
from tools.character_request_export import EYES, POSES, export_request


class RequestExportTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.hd, self.package = self.root / "hd", self.root / "package"
        for folder in (self.hd / "idle", self.hd / "look", self.hd / "waiting",
                       self.package / "waiting", self.package / "originale",
                       self.package / "masks", self.root / "frames/idle"):
            folder.mkdir(parents=True)
        reference = Image.new("RGBA", (384, 416))
        draw = ImageDraw.Draw(reference)
        draw.rectangle((103, 76, 279, 240), fill="white")
        draw.rectangle((140, 240, 240, 349), fill="blue")
        draw.rectangle((156, 350, 184, 387), fill="white")
        draw.rectangle((196, 350, 225, 387), fill="white")
        reference.save(self.hd / "idle/00.png")
        reference.save(self.hd / "look/00.png")
        Image.new("RGBA", (192, 208)).save(self.root / "frames/idle/00.png")
        idle_payload = (self.hd / "idle/00.png").read_bytes()
        head = Image.new("L", reference.size)
        ImageDraw.Draw(head).rectangle((103, 76, 279, 240), fill=255)
        head.save(self.package / "head-mask.png")
        eyes = Image.new("L", reference.size)
        ImageDraw.Draw(eyes).rectangle((145, 180, 180, 212), fill=255)
        eyes.save(self.package / "eye-mask.png")
        originals = {}
        for index, pose in enumerate(("A", "B", "C")):
            path = self.package / f"originale/{pose}.png"
            Image.new("RGBA", (1024, 1024), (index * 60, 120, 200, 255)).save(path)
            originals[pose] = {"sha256": sha256_digest(path.read_bytes()),
                               "size": [1024, 1024], "kind": "native-test-source"}
        frames = []
        for index, (pose, eye_phase) in enumerate(zip(POSES, EYES, strict=True)):
            relative = f"waiting/{index:02}.png"
            frame = reference.copy()
            mask = Image.new("L", reference.size)
            if pose != "idle":
                point = {"A": (145, 270), "B": (150, 275), "C": (155, 280)}[pose]
                frame.putpixel(point, (30, 190, 230, 255))
                mask.putpixel(point, 255)
            if eye_phase != "offen":
                frame.putpixel((160, 195), (10, 100, 200, 255)
                               if eye_phase == "halboffen" else (0, 0, 0, 255))
                mask.putpixel((160, 195), 255)
            path = self.package / relative
            if pose == "idle":
                path.write_bytes(idle_payload)
            else:
                frame.save(path)
            mask.save(self.package / f"masks/{index:02}.png")
            frames.append({"path": relative, "pose": pose, "eyes": eye_phase,
                           "sha256": sha256_digest(path.read_bytes()),
                           "allowed_mask_sha256": sha256_digest(
                               (self.package / f"masks/{index:02}.png").read_bytes()),
                           })
            (self.hd / relative).write_bytes(idle_payload)
        self.inputs = {
            "version": 1, "size": [384, 416],
            "reference_sha256": sha256_digest(idle_payload),
            "head_mask_sha256": sha256_digest(
                (self.package / "head-mask.png").read_bytes()),
            "eye_mask_sha256": sha256_digest(
                (self.package / "eye-mask.png").read_bytes()),
            "originals": originals, "frames": frames,
            "eye_provenance": {name: {"kind": "reused"} for name in set(EYES)},
        }
        self.write_inputs()
        self.other_records = [{"path": "idle/00.png", "preserved": "idle"},
                              {"path": "look/00.png", "preserved": "gaze"}]
        (self.hd / "manifest.json").write_text(json.dumps({
            "version": 1, "size": [384, 416],
            "frames": [*self.other_records, *[{"path": r["path"]} for r in frames]],
        }), "utf-8")
        self.before = {p: p.read_bytes() for p in self.root.rglob("*")
                       if p.is_file() and not p.is_relative_to(self.package)}

    def write_inputs(self) -> None:
        (self.package / "manifest.json").write_text(json.dumps(self.inputs), "utf-8")

    def assert_live_unchanged(self) -> None:
        for path, content in self.before.items():
            self.assertEqual(path.read_bytes(), content, str(path))

    def test_complete_import_preserves_endpoints_and_other_clips(self) -> None:
        records = export_request(self.package, self.hd)
        self.assertEqual(len(records), 8)
        manifest = json.loads((self.hd / "manifest.json").read_text("utf-8"))
        self.assertEqual(manifest["frames"][:2], self.other_records)
        for path in (self.hd / "idle/00.png", self.hd / "look/00.png",
                     self.root / "frames/idle/00.png"):
            self.assertEqual(path.read_bytes(), self.before[path])
        self.assertEqual((self.hd / "waiting/00.png").read_bytes(),
                         (self.hd / "waiting/07.png").read_bytes())
        self.assertEqual((self.hd / "waiting/01.png").read_bytes(),
                         (self.hd / "waiting/06.png").read_bytes())

    def test_small_native_source_is_rejected_before_any_replacement(self) -> None:
        path = self.package / "originale/B.png"
        Image.new("RGBA", (512, 1024), (10, 20, 30, 255)).save(path)
        data = json.loads((self.package / "manifest.json").read_text("utf-8"))
        data["originals"]["B"] = {"sha256": sha256_digest(path.read_bytes()),
                                  "size": [512, 1024]}
        (self.package / "manifest.json").write_text(json.dumps(data), "utf-8")
        with self.assertRaisesRegex(ValueError, "1000px"):
            export_request(self.package, self.hd)
        self.assert_live_unchanged()

    def test_missing_final_frame_never_partially_installs_the_animation(self) -> None:
        (self.package / "waiting/07.png").unlink()
        with self.assertRaises(FileNotFoundError):
            export_request(self.package, self.hd)
        self.assert_live_unchanged()

    def test_matching_frame_digest_cannot_bypass_protected_torso_pixels(self) -> None:
        path = self.package / "waiting/05.png"
        with Image.open(path) as image:
            image.putpixel((190, 300), (1, 2, 3, 255))
            image.save(path)
        data = json.loads((self.package / "manifest.json").read_text("utf-8"))
        data["frames"][5]["sha256"] = sha256_digest(path.read_bytes())
        (self.package / "manifest.json").write_text(json.dumps(data), "utf-8")
        with self.assertRaisesRegex(ValueError, "protected pixels"):
            export_request(self.package, self.hd)
        self.assert_live_unchanged()

    def test_signed_mask_cannot_expand_into_the_face_outside_the_eyes(self) -> None:
        path = self.package / "masks/04.png"
        with Image.open(path) as mask:
            mask.putpixel((192, 230), 255)
            mask.save(path)
        data = json.loads((self.package / "manifest.json").read_text("utf-8"))
        data["frames"][4]["allowed_mask_sha256"] = sha256_digest(path.read_bytes())
        (self.package / "manifest.json").write_text(json.dumps(data), "utf-8")
        with self.assertRaisesRegex(ValueError, "only eyes and arm/hand"):
            export_request(self.package, self.hd)
        self.assert_live_unchanged()


if __name__ == "__main__":
    unittest.main()
