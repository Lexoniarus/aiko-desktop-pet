"""Reviewed body packages install completely without changing either atlas."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools.character_body_pose_export import export_body_poses


class BodyPoseExportTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.package, self.assets = self.root / "package", self.root / "assets"
        self.package.mkdir()
        (self.package / "package.json").write_text(json.dumps({
            "head_offsets": {"left": [2, 3], "right": [-2, 3]},
        }), "utf-8")
        for side in ("left", "right"):
            self.save_source(f"body-{side}.png", (190, 300), (20, 40, 80, 255))
            for index in range(1, 5):
                self.save_source(f"turn-{side}/{index:02}.png", (190, 300),
                                 (index * 30, 80, 40, 255))
        for direction in range(16):
            self.save_source(f"heads/{direction:02}.png", (190, 150),
                             (direction * 10, 60, 120, 200))
        for relative, size in (("frames/idle/00.png", (192, 208)),
                               ("frames_2x/idle/00.png", (384, 416))):
            target = self.assets / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", size).save(target)
        existing = self.assets / "body_poses/manifest.json"
        existing.parent.mkdir()
        existing.write_text('{"existing": true}', "utf-8")
        self.before = {p.relative_to(self.assets): p.read_bytes()
                       for p in self.assets.rglob("*") if p.is_file()}

    def save_source(self, relative: str, point: tuple[int, int],
                    color: tuple[int, int, int, int]) -> None:
        target = self.package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (384, 416))
        image.putpixel(point, color)
        image.save(target)

    def assert_install_unchanged(self) -> None:
        self.assertEqual(
            {p.relative_to(self.assets): p.read_bytes()
             for p in self.assets.rglob("*") if p.is_file()}, self.before,
        )

    def test_complete_pack_composes_both_sides_and_preserves_legacy_atlases(self):
        manifest = export_body_poses(self.package, self.assets)
        self.assertEqual(len(list((self.assets / "body_poses").rglob("*.png"))), 26)
        for relative, payload in self.before.items():
            if relative.parts[0] != "body_poses":
                self.assertEqual((self.assets / relative).read_bytes(), payload)
        for side, x, direction in (("left", 192, 15), ("right", 188, 8)):
            with Image.open(self.assets / f"body_poses/body-look-{side}/08.png") as im:
                self.assertEqual(im.getpixel((x, 153)), (direction * 10, 60, 120, 255))
                self.assertEqual(im.getpixel((190, 300)), (20, 40, 80, 255))
            self.assertEqual(manifest["clips"][f"body-turn-{side}"][0],
                             "frames_2x/idle/00.png")
        written = json.loads((self.assets / "body_poses/manifest.json").read_text())
        self.assertEqual(written, manifest)

    def test_missing_last_source_does_not_replace_existing_pack(self) -> None:
        (self.package / "turn-right/04.png").unlink()
        with self.assertRaises(FileNotFoundError):
            export_body_poses(self.package, self.assets)
        self.assert_install_unchanged()

    def test_invalid_dimensions_do_not_create_an_install(self) -> None:
        Image.new("RGBA", (192, 208)).save(self.package / "body-left.png")
        target = self.root / "uninstalled"
        with self.assertRaisesRegex(ValueError, "384x416 RGBA"):
            export_body_poses(self.package, target)
        self.assertFalse(target.exists())

    def test_missing_idle_reference_preserves_existing_pack(self) -> None:
        (self.assets / "frames_2x/idle/00.png").unlink()
        self.before.pop(Path("frames_2x/idle/00.png"))
        with self.assertRaisesRegex(FileNotFoundError, "existing idle"):
            export_body_poses(self.package, self.assets)
        self.assert_install_unchanged()

    def test_png_encoding_failure_does_not_replace_existing_pack(self) -> None:
        save = Image.Image.save

        def fail_last(image, path, *args, **kwargs):
            if Path(path).as_posix().endswith("body-turn-right/04.png"):
                raise OSError("Cannot encode last frame")
            return save(image, path, *args, **kwargs)

        with patch.object(Image.Image, "save", fail_last):
            with self.assertRaisesRegex(OSError, "last frame"):
                export_body_poses(self.package, self.assets)
        self.assert_install_unchanged()
