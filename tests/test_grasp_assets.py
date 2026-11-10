"""The same approved HD grasp family is used at both display scales."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.grasp_assets import GRASP_CLIPS, load_grasp_clips
from scripts.build_room_package import runtime_assets


class GraspAssetsTests(unittest.TestCase):
    def test_complete_family_shares_hd_source_and_has_clean_alpha(self):
        catalog = load_character_catalog()
        for name in GRASP_CLIPS:
            clip = catalog.clip_for(name, 1)
            self.assertIs(clip, catalog.clip_for(name, 2))
            self.assertEqual(clip.item_anchor_mode, "center")
            self.assertFalse(clip.loop)
            for path in {f.file for f in clip.frames}:
                with Image.open(path) as im:
                    self.assertEqual(im.size, (384, 416))
                    self.assertEqual(set(im.getchannel("A").tobytes()), {0, 255})

    def test_inspection_markers_and_four_seconds_are_authored_not_guessed(self):
        clips = load_grasp_clips(ASSET_ROOT)
        at = 0
        markers = {}
        for f in clips["inspect_item"].frames:
            for event in f.events:
                markers[event] = at
            at += f.duration_ms
        self.assertEqual(markers, {"inspect_comment": 400, "inspect_emote": 850})
        self.assertEqual(sum(clips[n].duration_seconds for n in (
            "inspect_item", "inspect_hold", "inspect_return",
        )), 4)
        self.assertEqual(sum("attach_object" in f.events
                             for f in clips["pick_up"].frames), 1)
        self.assertEqual(sum("release_object" in f.events
                             for f in clips["throw_item"].frames), 1)

    def test_room_package_exports_every_new_clip_and_center_pivots(self):
        exported = runtime_assets("test-grasp", 0)["clips"]
        for name in GRASP_CLIPS:
            self.assertIn(name, exported)
            self.assertEqual(exported[name]["itemAnchorMode"], "center")
            self.assertTrue(all(f["file"].startswith("assets/actions/grasp/")
                                for f in exported[name]["frames"]))

    def test_loader_rejects_changed_png_before_any_runtime_starts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = json.loads((ASSET_ROOT / "actions/grasp.json").read_text("utf-8"))
            first = next(iter(data["clips"].values()))["frames"][0]
            target = root / first["file"]
            target.parent.mkdir(parents=True)
            target.write_bytes(b"changed")
            first["sha256"] = hashlib.sha256(b"original").hexdigest()
            (root / "actions/grasp.json").write_text(json.dumps(data), "utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_grasp_clips(root)
