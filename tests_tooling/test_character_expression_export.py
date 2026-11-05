"""Expression export preserves its sources and validates before writing."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from tools.character_expression_export import SOURCE_IDS, TARGET_IDS, export


class ExpressionExportTests(unittest.TestCase):

    def test_export_is_repeatable_and_validates_all_sources_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, destination = root / "source", root / "runtime"
            source.mkdir()
            installed = json.loads(
                (ASSET_ROOT / "expressions/manifest.json").read_text(),
            )
            clips = []
            for source_id, target_id in zip(SOURCE_IDS, TARGET_IDS, strict=True):
                row = installed["clips"][target_id]
                for frame in row["frames"]:
                    path = source / frame["file"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ASSET_ROOT / frame["file"], path)
                clips.append(dict(id=source_id, frames=row["frames"]))
            data: dict[str, Any] = dict(
                status="USER_VISUALLY_APPROVED_PREVIEW_COMPLETE", clips=clips,
            )
            manifest = source / "manifest.json"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            # Represent the near-opaque body pixels and faint detached alpha
            # remnants from ImageGen/assembly without relying on private jobs.
            first = data["clips"][0]["frames"][0]
            original_path = source / first["file"]
            with Image.open(original_path) as image:
                softened = image.convert("RGBA")
                softened.putalpha(softened.getchannel("A").point(
                    lambda value: 253 if value == 255 else 0,
                ))
                softened.putpixel((0, 0), (249, 0, 249, 3))
                softened.save(original_path)
            before_source = original_path.read_bytes()
            first["sha256"] = hashlib.sha256(before_source).hexdigest()
            manifest.write_text(json.dumps(data), encoding="utf-8")
            export(source, destination)
            self.assertEqual(original_path.read_bytes(), before_source)
            with (Image.open(original_path) as original,
                  Image.open(destination / first["file"]) as normalized):
                self.assertEqual(original.convert("RGB").tobytes(),
                                 normalized.convert("RGB").tobytes())
                self.assertEqual(sum(normalized.getchannel("A").histogram()[1:255]), 0)
                self.assertEqual(normalized.getchannel("A").getpixel((0, 0)), 0)
            before = {
                p.relative_to(destination): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in destination.rglob("*") if p.is_file()
            }
            export(source, destination)
            self.assertEqual(before, {
                p.relative_to(destination): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in destination.rglob("*") if p.is_file()
            })
            data["clips"][-1]["frames"][-1]["sha256"] = "0" * 64
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                export(source, root / "rejected")
            self.assertFalse((root / "rejected").exists())
