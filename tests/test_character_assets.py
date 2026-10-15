"""Validate runtime sprites, per-frame pacing and replay metadata."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.character_assets import load_character_catalog


class CharacterCatalogTests(unittest.TestCase):
    def test_eight_source_sprites_with_independent_playback(self) -> None:
        catalog = load_character_catalog()
        self.assertEqual(len(catalog.clips), 14)
        self.assertEqual(
            len({
                frame.file for clip in catalog.clips.values() for frame in clip.frames
            }),
            112,
        )
        self.assertNotIn("running", catalog.clips)
        self.assertEqual(catalog.clips["idle"].timings, (160,) * 8)
        self.assertAlmostEqual(catalog.clips["eat"].duration_seconds, 3.59)
        self.assertAlmostEqual(catalog.clips["waving"].duration_seconds, 1.135)
        self.assertAlmostEqual(
            catalog.clips["waving-greeting"].duration_seconds,
            1.895,
        )
        self.assertIs(
            catalog.clips["waving"].frames,
            catalog.clips["waving-greeting"].frames,
        )
        self.assertFalse(catalog.clips["eat"].loop)
        self.assertTrue(catalog.clips["sleep"].loop)
        self.assertEqual(catalog.clips["eat"].frames[3].events, ("bite",))
        self.assertEqual(len(catalog.clips["look"].frames), 16)
        self.assertEqual(
            catalog.clips["attack"].frames[3].events,
            ("attack_release",),
        )
        self.assertEqual(
            catalog.clips["attack"].timings,
            (215,) * 8,
        )
        self.assertGreater(
            catalog.clips["waiting"].duration_seconds,
            catalog.clips["idle"].duration_seconds,
        )

    def test_runtime_profile_matches_export_and_preserves_sources(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        policy = json.loads(
            (ASSET_ROOT / "animation_timing.json").read_text("utf-8"),
        )
        durations = policy["frame_duration_ms"]
        self.assertEqual(policy["version"], 3)
        self.assertEqual(durations["running-left"], [190] * 8)
        self.assertNotEqual(durations["sleep"], durations["waving"])
        self.assertEqual(len(data["animations"]), 13)
        for clip in data["animations"]:
            name = clip["state"]
            if name == "look":
                self.assertEqual(len(clip["frames"]), 16)
                self.assertNotIn("sequence", clip)
                continue
            frames = clip["frames"]
            with self.subTest(animation=name):
                self.assertEqual(len(frames), 8)
                self.assertEqual(
                    [frame["duration_ms"] for frame in frames],
                    durations[name],
                )
                sequence = policy["frame_sequences"].get(
                    name,
                    list(range(8)),
                )
                self.assertEqual(clip["sequence"], sequence)
                self.assertEqual(
                    clip["playback_total_ms"],
                    sum(durations[name][index] for index in sequence),
                )
                self.assertTrue(
                    all(type(frame["source_duration_ms"]) is int for frame in frames)
                )
                self.assertEqual(
                    [frame["file"].rsplit("/", 1)[1] for frame in frames],
                    [f"{i:02d}.png" for i in range(8)],
                )

    def test_frame_tempo_is_configurable_through_shared_policy(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        for entry in data["animations"]:
            if entry["state"] == "waving":
                entry["frames"][1]["duration_ms"] = 205
                order = entry["sequence"]
                entry["playback_total_ms"] = sum(
                    entry["frames"][index]["duration_ms"] for index in order
                )
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._write_catalog(root, data)
            path = root / "animation_timing.json"
            policy = json.loads(path.read_text("utf-8"))
            policy["frame_duration_ms"]["waving"][1] = 205
            path.write_text(json.dumps(policy), encoding="utf-8")
            catalog = load_character_catalog(root)
            clip = catalog.clips["waving"]
            self.assertEqual(clip.frames[1].duration_ms, 205)
            self.assertEqual(clip.sprite_index(1), 1)
            self.assertEqual(clip.timings[1], 205)
            greeting = catalog.clips["waving-greeting"]
            self.assertEqual(len(clip.timings), 8)
            self.assertEqual(greeting.timings[8], 115)
            self.assertEqual(greeting.timings[1], 205)
            self.assertAlmostEqual(
                catalog.clips["running-left"].duration_seconds,
                1.52,
            )

    def test_timing_policy_rejects_invalid_hold_values(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        for invalid in (0, -1, "160", 39, 5001, True):
            with self.subTest(value=invalid), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                self._write_catalog(root, data)
                path = root / "animation_timing.json"
                profile = json.loads(path.read_text("utf-8"))
                profile["frame_duration_ms"]["idle"][0] = invalid
                path.write_text(json.dumps(profile), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_character_catalog(root)

    def test_timing_policy_rejects_missing_or_extra_clips(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        for missing in (True, False):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                self._write_catalog(root, data)
                path = root / "animation_timing.json"
                profile = json.loads(path.read_text("utf-8"))
                if missing:
                    del profile["frame_duration_ms"]["idle"]
                else:
                    profile["frame_duration_ms"]["unknown"] = [160] * 8
                path.write_text(json.dumps(profile), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_character_catalog(root)

    def test_replay_order_rejects_invalid_poses_and_missing_assets(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        for invalid in ([], list(range(7)), [0] * 8, [0, 1, 2, 3, 4, 5, 6, 8]):
            with (
                self.subTest(sequence=invalid),
                tempfile.TemporaryDirectory() as folder,
            ):
                root = Path(folder)
                self._write_catalog(root, data)
                path = root / "animation_timing.json"
                profile = json.loads(path.read_text("utf-8"))
                profile["frame_sequences"]["waving"] = invalid
                path.write_text(json.dumps(profile), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_character_catalog(root)

    def test_greeting_variant_is_required_by_the_timing_policy(self) -> None:
        data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._write_catalog(root, data)
            path = root / "animation_timing.json"
            profile = json.loads(path.read_text("utf-8"))
            del profile["frame_sequences"]["waving-greeting"]
            path.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_character_catalog(root)

    def _write_catalog(self, root: Path, data: dict[str, Any]) -> None:
        for clip in data["animations"]:
            for frame in clip["frames"]:
                path = (root / frame["file"]).resolve()
                if path.is_relative_to(root.resolve()):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
        (root / "animations.json").write_text(
            json.dumps(data),
            encoding="utf-8",
        )
        (root / "animation_timing.json").write_bytes(
            (ASSET_ROOT / "animation_timing.json").read_bytes(),
        )

    def test_corrupt_metadata_and_escaping_paths_are_rejected(self) -> None:
        for broken in (
            "duration",
            "mismatch",
            "count",
            "path",
            "loop",
            "return_to",
            "gaze",
            "sequence",
        ):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as folder:
                data = json.loads((ASSET_ROOT / "animations.json").read_text("utf-8"))
                entry = data["animations"][0]
                if broken == "duration":
                    entry["frames"][0]["duration_ms"] = 0
                elif broken == "mismatch":
                    entry["frames"][2]["duration_ms"] += 1
                elif broken == "count":
                    entry["frames"].pop()
                elif broken == "path":
                    entry["frames"][0]["file"] = "../outside.png"
                elif broken == "loop":
                    entry["loop"] = "false"
                elif broken == "return_to":
                    entry["return_to"] = "unknown"
                elif broken == "sequence":
                    entry["sequence"].pop()
                else:
                    data["animations"][-1]["frames"].pop()
                root = Path(folder)
                self._write_catalog(root, data)
                with self.assertRaises(ValueError):
                    load_character_catalog(root)
