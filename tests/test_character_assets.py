"""Validate imported runtime clips and reject malformed catalog boundaries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.character_assets import load_character_catalog


class CharacterCatalogTests(unittest.TestCase):
    def test_new_clips_keep_authored_timing_and_gaze_order(self) -> None:
        catalog = load_character_catalog()
        self.assertEqual(sum(len(c.frames) for c in catalog.clips.values()), 112)
        self.assertNotIn("running", catalog.clips)
        self.assertEqual(catalog.clips["idle"].timings,
                         (280, 110, 60, 50, 70, 70, 140, 320))
        self.assertEqual(catalog.clips["eat"].duration_seconds, 2.3)
        self.assertFalse(catalog.clips["eat"].loop)
        self.assertTrue(catalog.clips["sleep"].loop)
        self.assertEqual(catalog.clips["eat"].frames[3].events, ("bite",))
        self.assertEqual(len(catalog.clips["look"].frames), 16)
        self.assertEqual(catalog.clips["attack"].frames[3].events,
                         ("attack_release",))

    def _write_catalog(self, root: Path, data: dict[str, Any]) -> None:
        for clip in data["animations"]:
            for frame in clip["frames"]:
                path = (root / frame["file"]).resolve()
                if path.is_relative_to(root.resolve()):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
        (root / "animations.json").write_text(json.dumps(data), encoding="utf-8")

    def test_corrupt_metadata_and_escaping_paths_are_rejected(self) -> None:
        for broken in ("duration", "path", "loop", "return_to", "gaze"):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as folder:
                data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
                entry = data["animations"][0]
                if broken == "duration":
                    entry["frames"][0]["duration_ms"] = 0
                elif broken == "path":
                    entry["frames"][0]["file"] = "../outside.png"
                elif broken == "loop":
                    entry["loop"] = "false"
                elif broken == "return_to":
                    entry["return_to"] = "unknown"
                else:
                    data["animations"][-1]["frames"].pop()
                root = Path(folder)
                self._write_catalog(root, data)
                with self.assertRaises(ValueError):
                    load_character_catalog(root)
