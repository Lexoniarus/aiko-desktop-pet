"""Animation timing policy is pure; filesystem loading belongs to infrastructure."""

import json
import unittest

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.animation_timing import load_timing_policy
from aiko_pet.pet.animation.timing import (
    AnimationTimingPolicy,
    VIRTUAL_CLIPS,
    parse_timing_policy,
)


class AnimationTimingBoundaryTests(unittest.TestCase):
    def test_timing_policy_is_owned_by_pet_domain(self) -> None:
        self.assertEqual(AnimationTimingPolicy.__module__, "aiko_pet.pet.animation.timing")

    def test_pure_validation_matches_both_loaders(self) -> None:
        raw = json.loads(
            (ASSET_ROOT / "animation_timing.json").read_text("utf-8"),
        )
        expected = parse_timing_policy(raw)
        canonical = load_timing_policy(ASSET_ROOT)
        self.assertEqual(canonical.frame_ms, expected.frame_ms)
        self.assertEqual(canonical.sequences, expected.sequences)
        self.assertEqual(dict(VIRTUAL_CLIPS), {"waving-greeting": "waving"})

    def test_rejects_invalid_profile_without_touching_files(self) -> None:
        with self.assertRaises(ValueError):
            parse_timing_policy({"version": 3})
