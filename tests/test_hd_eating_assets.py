"""HD meals are validated separately from the unchanged legacy sprite atlas."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiko_pet.infrastructure.eating_assets import load_hd_eating_clip
from aiko_pet.pet.animation.character import (
    AnimationClip,
    AnimationFrame,
    CharacterCatalog,
)


class HdEatingAssetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        target = self.root / "actions/eat/pose.png"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"fixture; image dimensions checked by sprite cache")
        self.row = {"file": "actions/eat/pose.png", "duration_ms": 400,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    "food_anchor": [96, 140], "events": []}
        self.data = {"version": 1, "size": [384, 416], "anchor": [96, 194],
                     "frames": [dict(self.row) for _ in range(15)]}
        for index in (3, 7, 11):
            self.data["frames"][index]["events"] = ["bite"]
        for index in range(11, 15):
            self.data["frames"][index]["food_anchor"] = None

    def save(self):
        (self.root / "actions/eat.json").write_text(json.dumps(self.data), "utf-8")

    def test_approved_three_bite_clip_is_shared_by_both_display_sizes(self):
        self.save()
        hd = load_hd_eating_clip(self.root)
        legacy = AnimationClip("eat", (AnimationFrame(Path("old.png"), 100),),
                               False, (96, 196))
        catalog = CharacterCatalog({"eat": legacy}, hd_action_clips=hd)
        meal = catalog.clip_for("eat", 2)
        self.assertIs(catalog.clip_for("eat", 1), meal)
        self.assertEqual(meal.duration_seconds, 6)
        self.assertEqual(sum(f.events == ("bite",) for f in meal.frames), 3)
        self.assertIsNone(meal.frames[11].food_anchor)
        self.assertTrue(all(f.food_anchor for f in meal.frames[:11]))

    def test_absent_pack_keeps_old_installations_valid(self):
        self.assertFalse(load_hd_eating_clip(self.root))

    def test_invalid_meals_fail_before_display(self):
        mutations = (
            lambda d: d.update(anchor=[96, 196]),
            lambda d: d["frames"][0].update(file="../outside.png"),
            lambda d: d["frames"][0].update(sha256="0" * 64),
            lambda d: d["frames"][0].update(duration_ms=True),
            lambda d: d["frames"][0].update(food_anchor=[False, 140]),
            lambda d: d["frames"][0].update(food_anchor=None),
            lambda d: d["frames"][-1].update(food_anchor=[96, 140]),
            lambda d: d["frames"][7].update(events=[]),
            lambda d: d["frames"][1].update(events=["bite"]),
            lambda d: d["frames"][1].update(events=["consume"]),
        )
        pristine = json.dumps(self.data)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.data = json.loads(pristine)
                mutation(self.data)
                self.save()
                with self.assertRaises(ValueError):
                    load_hd_eating_clip(self.root)
