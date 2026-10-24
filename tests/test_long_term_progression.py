"""Long-term episodes share the actual save/elapsed-time integration path."""

import copy
import unittest

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.moodlets import MoodletCauseKind, MoodletId
from aiko_pet.pet.state import PetState

WALL = 1800000000
DAY = 86400


class LongTermProgressionTests(unittest.TestCase):
    def test_closed_time_and_split_reload_account_same_period_once(self):
        whole = PetState(updated_at=WALL)
        divided = copy.deepcopy(whole)
        whole.advance(WALL + DAY, observed=False)
        for seconds in (4 * 3600, 12 * 3600, DAY):
            divided.advance(WALL + seconds, observed=False)
            divided = decode_pet_state(
                encode_pet_state(divided), now=divided.updated_at
            )
        actual = next(
            e for e in whole.moodlets.active if e.definition_id == MoodletId.OVERLOOKED
        )
        other = next(
            e
            for e in divided.moodlets.active
            if e.definition_id == MoodletId.OVERLOOKED
        )
        self.assertEqual(actual, other)
        self.assertEqual(actual.level, 1)
        self.assertEqual(whole.moodlets.care_evidence, divided.moodlets.care_evidence)
        before = encode_pet_state(divided)
        divided.advance(divided.updated_at, observed=False)
        self.assertEqual(encode_pet_state(divided), before)
        self.assertFalse(whole.moodlets.care_evidence.experiences)

    def test_long_term_decay_is_not_frozen_by_capped_zero_need_optimization(self):
        pet = PetState(updated_at=WALL)
        pet.advance(WALL + DAY, observed=False)
        pet.advance(WALL + DAY + 60, observed=False)
        episode = next(
            e for e in pet.moodlets.active if e.definition_id == MoodletId.OVERLOOKED
        )
        self.assertAlmostEqual(episode.remaining_seconds, 30 * 3600 - 60, places=5)
        for poor in pet.moodlets.active:
            if poor.definition_id != MoodletId.OVERLOOKED:
                self.assertTrue(
                    all(c.kind == MoodletCauseKind.POOR_CARE for c in poor.causes)
                )
                self.assertTrue(all(c.target_id is not None for c in poor.causes))

    def test_absence_continues_without_creating_fictional_personal_encounters(self):
        pet = PetState(updated_at=WALL)
        pet.advance(WALL + 3 * DAY, observed=False)
        episode = next(
            e for e in pet.moodlets.active if e.definition_id == MoodletId.OVERLOOKED
        )
        self.assertEqual(episode.level, 3)
        self.assertEqual(len(episode.causes), 3)
        for cause, start in zip(episode.causes, (0, DAY, 2 * DAY), strict=True):
            self.assertAlmostEqual(cause.period.started_at, start, places=5)
        self.assertFalse(pet.moodlets.care_evidence.encounters)
        self.assertEqual(
            decode_pet_state(encode_pet_state(pet), now=pet.updated_at).moodlets,
            pet.moodlets,
        )


if __name__ == "__main__":
    unittest.main()
