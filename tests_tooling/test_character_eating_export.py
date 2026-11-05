"""V3 eating export preserves geometry and unrelated prepared artwork."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.character_eating_export import export_eating, register_pose


def source_pose() -> Image.Image:
    image = Image.new("RGBA", (1152, 1248))
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((300, 100, 850, 500), fill=(230, 240, 250, 255))
    drawing.rectangle((450, 500, 700, 950), fill=(20, 40, 100, 255))
    drawing.rectangle((450, 950, 540, 1147), fill=(240, 240, 240, 255))
    drawing.rectangle((610, 950, 700, 1147), fill=(240, 240, 240, 255))
    return image


class EatingRegistrationTests(unittest.TestCase):
    def test_uniform_scale_and_foot_registration_without_clipping(self) -> None:
        result, info = register_pose(source_pose())
        self.assertEqual(result.size, (384, 416))
        self.assertEqual(set(result.getchannel("A").tobytes()), {0, 255})
        bounds = result.getchannel("A").getbbox()
        assert bounds is not None
        self.assertEqual(bounds[3], 392)
        self.assertEqual(bounds[3] - bounds[1], 312)
        shoes = result.getchannel("A").crop((0, 360, 384, 392)).getbbox()
        assert shoes is not None
        self.assertLessEqual(abs((shoes[0] + shoes[2]) / 2 - 192), 0.5)
        ratio = info["aspect_rescale_ratio"]
        assert isinstance(ratio, float)
        self.assertAlmostEqual(ratio, 1, delta=0.004)

    def test_empty_source_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Empty"):
            register_pose(Image.new("RGBA", (1200, 1200)))


class EatingExportTests(unittest.TestCase):
    def setUp(self) -> None:
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.originals = self.root / "originals"
        self.originals.mkdir()
        self.hd = self.root / "frames_2x"
        (self.hd / "eat").mkdir(parents=True)
        (self.hd / "idle").mkdir()
        Image.new("RGBA", (384, 416), (1, 2, 3, 255)).save(
            self.hd / "idle/00.png",
        )
        self.idle_bytes = (self.hd / "idle/00.png").read_bytes()
        records: list[dict[str, object]] = [
            {"path": "idle/00.png", "status": "unchanged-idle"},
        ]
        source = source_pose()
        for number in range(8):
            source.save(self.originals / f"{number + 1:02}.png")
            Image.new("RGBA", (384, 416)).save(
                self.hd / f"eat/{number:02}.png",
            )
            records.append({"path": f"eat/{number:02}.png", "old": True})
        self.manifest = {"version": 1, "size": [384, 416], "frames": records}
        (self.hd / "manifest.json").write_text(
            json.dumps(self.manifest), encoding="utf-8",
        )

    def test_complete_export_updates_eight_hashes_and_preserves_other_records(
        self,
    ) -> None:
        original_hash = hashlib.sha256(
            (self.originals / "01.png").read_bytes(),
        ).hexdigest()
        records = export_eating(self.originals, self.hd)
        manifest = json.loads((self.hd / "manifest.json").read_text("utf-8"))
        self.assertEqual(len(records), 8)
        self.assertEqual(manifest["frames"][0], self.manifest["frames"][0])
        self.assertEqual((self.hd / "idle/00.png").read_bytes(), self.idle_bytes)
        self.assertEqual(records[0]["source_sha256"], original_hash)
        self.assertEqual(records[-1]["reused_from_frame"], "eat/00.png")
        self.assertEqual(
            records[-1]["status"], "reused_v3_eating_individual_original",
        )
        for record in records:
            relative = record["path"]
            assert isinstance(relative, str)
            self.assertEqual(
                hashlib.sha256((self.hd / relative).read_bytes()).hexdigest(),
                record["sha256"],
            )

    def test_missing_last_original_does_not_replace_any_productive_file(
        self,
    ) -> None:
        before = {path: path.read_bytes() for path in self.hd.rglob("*")
                  if path.is_file()}
        (self.originals / "08.png").unlink()
        with self.assertRaises(FileNotFoundError):
            export_eating(self.originals, self.hd)
        self.assertTrue(all(path.read_bytes() == value
                            for path, value in before.items()))
