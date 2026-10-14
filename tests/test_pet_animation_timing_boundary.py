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
from aiko_pet.presentation.animation_timing import (
    AnimationTimingPolicy as LegacyTimingPolicy,
)
from aiko_pet.presentation.animation_timing import (
    load_timing_policy as legacy_load_timing_policy,
)


class AnimationTimingBoundaryTests(unittest.TestCase):
    def test_legacy_class_is_identical_to_canonical_policy(self) -> None:
        self.assertIs(AnimationTimingPolicy, LegacyTimingPolicy)

    def test_pure_validation_matches_both_loaders(self) -> None:
        raw = json.loads(
            (ASSET_ROOT / "animation_timing.json").read_text("utf-8"),
        )
        expected = parse_timing_policy(raw)
        canonical = load_timing_policy(ASSET_ROOT)
        legacy = legacy_load_timing_policy(ASSET_ROOT)
        self.assertEqual(canonical.frame_ms, expected.frame_ms)
        self.assertEqual(legacy.sequences, expected.sequences)
        self.assertEqual(dict(VIRTUAL_CLIPS), {"waving-greeting": "waving"})

    def test_rejects_invalid_profile_without_touching_files(self) -> None:
        with self.assertRaises(ValueError):
            parse_timing_policy({"version": 3})
