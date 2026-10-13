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
        self.assertEqual(catalog.clips["idle"].timings, (160,) * 8)
        self.assertEqual(catalog.clips["eat"].duration_seconds, 1.28)
        self.assertFalse(catalog.clips["eat"].loop)
        self.assertTrue(catalog.clips["sleep"].loop)
        self.assertEqual(catalog.clips["eat"].frames[3].events, ("bite",))
        self.assertEqual(len(catalog.clips["look"].frames), 16)
        self.assertEqual(catalog.clips["attack"].frames[3].events,
                         ("attack_release",))

    def test_uniform_pacing_preserves_original_source_frame_metadata(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        policy = json.loads(
            (ASSET_ROOT / "animation_timing.json").read_text("utf-8"),
        )
        duration = policy["regular_frame_duration_ms"]
        self.assertEqual(duration, 160)
        self.assertEqual(len(data["animations"]), 13)
        for clip in data["animations"]:
            name = clip["state"]
            if name == "look":
                self.assertEqual(len(clip["frames"]), 16)
                continue
            frames = clip["frames"]
            with self.subTest(animation=name):
                self.assertEqual(len(frames), 8)
                self.assertEqual(
                    [frame["duration_ms"] for frame in frames],
                    [duration] * 8,
                )
                self.assertTrue(all(
                    type(frame["source_duration_ms"]) is int
                    for frame in frames
                ))
                self.assertEqual(
                    [frame["file"].rsplit("/", 1)[1] for frame in frames],
                    [f"{i:02d}.png" for i in range(8)],
                )

    def test_tempo_is_configurable_through_the_shared_policy(self) -> None:
        """A different valid tempo works only when all clips agree with it."""
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        for clip in data["animations"]:
            if clip["state"] != "look":
                for frame in clip["frames"]:
                    frame["duration_ms"] = 200
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._write_catalog(root, data)
            config = root / "animation_timing.json"
            profile = json.loads(config.read_text("utf-8"))
            profile["regular_frame_duration_ms"] = 200
            config.write_text(json.dumps(profile), encoding="utf-8")
            catalog = load_character_catalog(root)
            self.assertEqual(catalog.clips["waving"].timings, (200,) * 8)
            self.assertEqual(catalog.clips["running-left"].duration_seconds, 1.6)

    def test_timing_policy_rejects_invalid_hold_values(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        for invalid in (0, -1, "160", 39, 1001):
            with self.subTest(value=invalid), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                self._write_catalog(root, data)
                path = root / "animation_timing.json"
                config = json.loads(path.read_text("utf-8"))
                config["regular_frame_duration_ms"] = invalid
                path.write_text(json.dumps(config), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_character_catalog(root)

    def _write_catalog(self, root: Path, data: dict[str, Any]) -> None:
        for clip in data["animations"]:
            for frame in clip["frames"]:
                path = (root / frame["file"]).resolve()
                if path.is_relative_to(root.resolve()):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
        (root / "animations.json").write_text(json.dumps(data), encoding="utf-8")
        (root / "animation_timing.json").write_bytes(
            (ASSET_ROOT / "animation_timing.json").read_bytes(),
        )

    def test_corrupt_metadata_and_escaping_paths_are_rejected(self) -> None:
        for broken in (
            "duration", "uneven", "count", "path", "loop", "return_to",
            "gaze",
        ):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as folder:
                data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
                entry = data["animations"][0]
                if broken == "duration":
                    entry["frames"][0]["duration_ms"] = 0
                elif broken == "uneven":
                    entry["frames"][2]["duration_ms"] += 1
                elif broken == "count":
                    entry["frames"].pop()
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
