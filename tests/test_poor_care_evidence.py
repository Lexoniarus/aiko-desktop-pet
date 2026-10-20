"""Shared exposure reader and bounded emotional watermarks, without ageing."""

import copy
import unittest
from dataclasses import replace

from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.friendship_decay import advance_friendship
from aiko_pet.pet.friendship_history import (
    CriticalBucket,
    FriendshipHistory,
    FriendshipProgress,
)
from aiko_pet.pet.moodlets import MoodletState, PoorCareCursor, PoorCareEvidence
from aiko_pet.pet.need_exposure import (
    ExposureMark,
    exposure_totals,
    mark_exposure,
    unaccounted_exposure,
)
from aiko_pet.pet.state import PetState


class PoorCareEvidenceTests(unittest.TestCase):
    def test_partial_anchor_minute_and_later_coalescing_preserve_exact_exposure(self):
        progress = FriendshipProgress(50, FriendshipHistory(baseline=0), 0)
        low = (0, 100, 100, 100, 100)
        progress = advance_friendship(progress, 25, low, low, sleeping=False)
        mark = mark_exposure(progress.history.critical, 25, 0)
        self.assertEqual(mark, ExposureMark(25, 25, 25))
        progress = advance_friendship(progress, 155, low, low, sleeping=False)
        self.assertEqual(len(progress.history.critical), 1)
        self.assertEqual(unaccounted_exposure(progress.history.critical, 180, 0, mark),
                         (155, 155))
        self.assertEqual(exposure_totals(progress.history.critical, 180)[0][0], 180)

    def test_mixed_partial_minute_and_rolling_expiry_use_one_original_history(self):
        buckets = (CriticalBucket(0, (40, 0, 0, 0, 0), (10, 0, 0, 0, 0)),)
        mark = ExposureMark(25, 15, 5)
        self.assertEqual(unaccounted_exposure(buckets, 60, 0, mark), (25, 5))
        self.assertEqual(unaccounted_exposure(buckets, 86500, 0, mark), (0, 0))

    def evidence(self):
        mark = ExposureMark(100, 10, 5)
        cursor = PoorCareCursor(mark, ExposureMark(200, 20, 10), 1, True)
        return PoorCareEvidence(100, (cursor,) * 5)

    def test_fixed_watermarks_round_trip_and_checkpoint_restore(self):
        state = PetState(lived_seconds=300, moodlets=MoodletState(
            poor_care=self.evidence(),
        ))
        checkpoint = state.capture_checkpoint()
        encoded = encode_pet_state(state)
        self.assertEqual(decode_pet_state(encoded).moodlets, state.moodlets)
        state.restore_checkpoint(replace(checkpoint, moodlets=MoodletState()))
        state.restore_checkpoint(checkpoint)
        self.assertEqual(state.moodlets.poor_care, self.evidence())
        encoded["moodlets"]["poor_care"]["needs"]["satiety"]["handled"]["at"] = 301
        self.assertIsNone(decode_pet_state(encoded).moodlets.poor_care)
        self.assertEqual(decode_pet_state(encoded).friendship, state.friendship)

    def test_legacy_defaults_and_invalid_markers_do_not_claim_emotional_history(self):
        state = MoodletState()
        saved = encode_moodlets(state)
        self.assertNotIn("poor_care", saved)
        self.assertEqual(decode_moodlets(saved, 300), state)
        valid = encode_moodlets(replace(state, poor_care=self.evidence()))
        for key, value in (("handled_level", True), ("handled_level", 4),
                           ("exposed", 1), ("accounted", {"at": 99}),
                           ("handled", {"at": 200, "critical": 61, "zero": 0})):
            broken = copy.deepcopy(valid)
            broken["poor_care"]["needs"]["satiety"][key] = value
            with self.assertRaises(ValueError):
                decode_moodlets(broken, 300)
