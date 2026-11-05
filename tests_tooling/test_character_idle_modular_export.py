"""Eye-only Idle installation cannot replace body pixels or unrelated clips."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.character_export_common import sha256_digest
from tools.character_idle_modular_export import PHASES, export_modular_idle


class ModularIdleExportTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.hd, self.package = self.root / "hd", self.root / "package"
        for directory in (self.hd / "idle", self.hd / "look",
                          self.package / "idle", self.package / "eyes"):
            directory.mkdir(parents=True)
        reference = Image.new("RGBA", (384, 416))
        drawing = ImageDraw.Draw(reference)
        drawing.rectangle((103, 76, 279, 240), fill="white")
        drawing.rectangle((140, 240, 240, 387), fill="blue")
        reference.save(self.hd / "idle/00.png")
        reference.save(self.hd / "look/00.png")
        reference_payload = (self.hd / "idle/00.png").read_bytes()
        body = reference.copy()
        body.paste((0, 0, 0, 0), (0, 0, 384, 260))
        body.save(self.package / "body.png")
        head = reference.copy()
        head.paste((0, 0, 0, 0), (0, 260, 384, 416))
        head.save(self.package / "head.png")
        mask = Image.new("L", reference.size)
        ImageDraw.Draw(mask).rectangle((145, 180, 180, 212), fill=255)
        mask.save(self.package / "eye-mask.png")
        phases = {}
        for phase, color in (("offen", "white"), ("halboffen", "cyan"),
                             ("geschlossen", "black")):
            image = reference.copy()
            ImageDraw.Draw(image).rectangle((150, 195, 170, 200), fill=color)
            if phase == "offen":
                (self.package / f"eyes/{phase}.png").write_bytes(reference_payload)
            else:
                image.save(self.package / f"eyes/{phase}.png")
            phases[phase] = (self.package / f"eyes/{phase}.png").read_bytes()
        frames = []
        for index, phase in enumerate(PHASES):
            relative = f"idle/{index:02}.png"
            (self.hd / relative).write_bytes(reference_payload)
            (self.package / relative).write_bytes(phases[phase])
            frames.append({"path": relative, "phase": phase,
                           "sha256": sha256_digest(phases[phase]),
                           "eye_sha256": sha256_digest(phases[phase]),
                           "eye_provenance": {"kind": "test"}})
        self.inputs = {
            "version": 1, "size": [384, 416],
            "reference_sha256": sha256_digest(reference_payload),
            "body_sha256": sha256_digest((self.package / "body.png").read_bytes()),
            "head_sha256": sha256_digest((self.package / "head.png").read_bytes()),
            "eye_mask_sha256": sha256_digest(
                (self.package / "eye-mask.png").read_bytes()),
            "frames": frames,
        }
        self.write_inputs()
        self.look_record = {"path": "look/00.png", "preserved": "calibrated-gaze"}
        (self.hd / "manifest.json").write_text(json.dumps({
            "version": 1, "size": [384, 416],
            "frames": [self.look_record, *[{"path": r["path"]} for r in frames]],
        }), "utf-8")
        self.before = {path: path.read_bytes() for path in self.hd.rglob("*")
                       if path.is_file()}

    def write_inputs(self) -> None:
        (self.package / "manifest.json").write_text(json.dumps(self.inputs), "utf-8")

    def assert_live_unchanged(self) -> None:
        for path, content in self.before.items():
            self.assertEqual(path.read_bytes(), content, str(path))

    def test_install_preserves_gaze_record_reference_and_open_endpoints(self) -> None:
        records = export_modular_idle(self.package, self.hd)
        self.assertEqual(len(records), 8)
        manifest = json.loads((self.hd / "manifest.json").read_text("utf-8"))
        self.assertEqual(manifest["frames"][0], self.look_record)
        for path in (self.hd / "look/00.png", self.hd / "idle/00.png",
                     self.hd / "idle/07.png"):
            self.assertEqual(path.read_bytes(), self.before[path])

    def test_missing_last_input_never_replaces_earlier_live_frames(self) -> None:
        (self.package / "idle/07.png").unlink()
        with self.assertRaises(FileNotFoundError):
            export_modular_idle(self.package, self.hd)
        self.assert_live_unchanged()

    def test_signed_frame_cannot_change_body_outside_eye_mask(self) -> None:
        path = self.package / "idle/04.png"
        with Image.open(path) as image:
            image.putpixel((190, 300), (1, 2, 3, 255))
            image.save(path)
        inputs = json.loads((self.package / "manifest.json").read_text("utf-8"))
        inputs["frames"][4]["sha256"] = sha256_digest(path.read_bytes())
        (self.package / "manifest.json").write_text(json.dumps(inputs), "utf-8")
        with self.assertRaisesRegex(ValueError, "outside the eyes"):
            export_modular_idle(self.package, self.hd)
        self.assert_live_unchanged()

    def test_mask_cannot_expand_into_the_body_even_with_matching_digest(self) -> None:
        path = self.package / "eye-mask.png"
        with Image.open(path) as mask:
            mask.putpixel((190, 300), 255)
            mask.save(path)
        self.inputs["eye_mask_sha256"] = sha256_digest(path.read_bytes())
        self.write_inputs()
        with self.assertRaisesRegex(ValueError, "reviewed eye region"):
            export_modular_idle(self.package, self.hd)
        self.assert_live_unchanged()


if __name__ == "__main__":
    unittest.main()
