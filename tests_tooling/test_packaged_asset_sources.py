"""Source integrity and reproducible authoring outputs, outside application runs."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT, PLAYING_CARDS_DIR
from aiko_pet.games.playing_cards import STANDARD_DECK
from aiko_pet.pet.catalog_validation import load_json
from tools.export_vn_ui import nine_slice

ROOT = Path(__file__).resolve().parents[1]


class PackagedSourceTests(unittest.TestCase):
    @unittest.skipIf(Image is None, "Pillow is needed only for asset preparation tests")
    def test_all_display_copies_have_binary_alpha_and_unchanged_geometry_and_rgb(self):
        root = ASSET_ROOT / "items"
        provenance = json.loads((root / "display/provenance.json").read_text("utf-8"))
        self.assertEqual(len(provenance["files"]), 22)
        assert Image is not None
        for record in provenance["files"]:
            source, display = (root / record["source"], root / record["display"])
            self.assertEqual(
                hashlib.sha256(source.read_bytes()).hexdigest(), record["source_sha256"]
            )
            self.assertEqual(
                hashlib.sha256(display.read_bytes()).hexdigest(),
                record["display_sha256"],
            )
            with Image.open(source) as raw, Image.open(display) as prepared:
                original, result = (raw.convert("RGBA"), prepared.convert("RGBA"))
                self.assertEqual(original.size, result.size)
                self.assertLessEqual(set(result.getchannel("A").tobytes()), {0, 255})
                self.assertEqual(
                    original.convert("RGB").tobytes(), result.convert("RGB").tobytes()
                )

    @unittest.skipIf(Image is None, "Pillow is needed only for asset preparation tests")
    def test_preparation_rebuilds_missing_outputs_and_is_reproducible(self):
        from shutil import copy2

        from tools.prepare_item_display_assets import prepare

        source_root = ASSET_ROOT / "items"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = json.loads((source_root / "items.json").read_text("utf-8"))
            (root / "items.json").write_text(json.dumps(data), encoding="utf-8")
            for item in data["foods"]:
                for variant in item["variants"].values():
                    path = root / variant["path"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    copy2(source_root / variant["path"], path)
            prepare(root)
            first = {
                path.relative_to(root): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            prepare(root)
            self.assertEqual(
                first,
                {
                    path.relative_to(root): path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file()
                },
            )

    def test_selected_source_export_matches_rebuild_inputs_and_hashes(self) -> None:
        bundle = ROOT / "assets/aiko-anime-8-frames"
        record = json.loads((bundle / "IMPORT_MANIFEST.json").read_text("utf-8"))
        originals = record["original_files"]
        self.assertEqual(len(originals), 134)
        self.assertEqual(
            sum((item["bytes"] for item in originals)), record["original_total_bytes"]
        )
        source = bundle / "aiko-anime-compact/animations-8"
        catalog_file = source / "catalog.json"
        catalog = json.loads(catalog_file.read_text("utf-8"))
        inputs = {catalog_file}
        for entry in catalog["animations"]:
            if entry["state"] == "running":
                continue
            manifest = source / entry["manifest"]
            inputs.add(manifest)
            clip = json.loads(manifest.read_text("utf-8"))
            for frame in clip["frames"]:
                inputs.add(manifest.parent / frame["file"])
                if "hand_foreground" in frame:
                    inputs.add(manifest.parent / frame["hand_foreground"])
        directions_file = source / catalog["look_directions"]
        inputs.add(directions_file)
        directions = json.loads(directions_file.read_text("utf-8"))
        inputs.update(
            (
                directions_file.parent / frame["file"]
                for frame in directions["directions"]
            )
        )
        self.assertEqual({bundle / item["path"] for item in originals}, inputs)
        for item in originals:
            path = bundle / item["path"]
            with self.subTest(path=item["path"]):
                content = path.read_bytes()
                self.assertEqual(len(content), item["bytes"])
                self.assertEqual(hashlib.sha256(content).hexdigest(), item["sha256"])

    def test_nine_slice_preserves_caps_and_transparent_center(self):
        source = Image.new("RGBA", (80, 20))
        source.putpixel((0, 0), (255, 0, 0, 255))
        output = nine_slice(source, (160, 20))
        self.assertEqual(output.getpixel((0, 0)), (255, 0, 0, 255))
        self.assertEqual(output.getchannel("A").getpixel((80, 10)), 0)

    def test_ui_source_hashes_match_the_export_manifest(self):
        catalog = load_json(ASSET_ROOT / "ui/catalog.json")
        self.assertTrue(catalog["source_sha256"])
        for path, expected in catalog["source_sha256"].items():
            with self.subTest(path=path):
                self.assertEqual(
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected
                )

    def test_card_sources_match_their_manifest_and_license(self):
        manifest = json.loads((PLAYING_CARDS_DIR / "provenance.json").read_text())
        names = {card.asset_name for card in STANDARD_DECK} | {"card_back.png"}
        self.assertEqual(set(manifest["files"]), names)
        self.assertEqual(manifest["license"], "CC0-1.0")
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(
                    hashlib.sha256((PLAYING_CARDS_DIR / name).read_bytes()).hexdigest(),
                    manifest["files"][name],
                )
