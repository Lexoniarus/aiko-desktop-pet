"""Approved pickup source bundle is complete and byte-preserved."""

import hashlib
import json
import struct
import unittest
from pathlib import Path


class PickupSourceTests(unittest.TestCase):
    def test_approved_runtime_sources_and_hands_match_import_manifest(self):
        root = Path(__file__).resolve().parents[1] / "assets/aiko-pick-up"
        record = json.loads((root / "IMPORT_MANIFEST.json").read_text("utf-8"))
        self.assertEqual(len(record["files"]), 21)
        for entry in record["files"]:
            raw = (root / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
            if entry["path"].endswith(".png"):
                self.assertEqual(struct.unpack(">II", raw[16:24]), (192, 208))
        clip = json.loads((root / "animation.json").read_text("utf-8"))
        self.assertEqual(clip["feet_anchor"], [96, 196])
        self.assertEqual(clip["playback"]["pick_up"]["attach_at"], 4)
