"""Regression tests for friendship policy and persisted value normalization."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.friendship import FRIENDSHIP_DAILY_CAP
from aiko_pet.pet.state import PetState
from aiko_pet.pet.value_rules import clamp_saved_time


def stamp(day: int = 12, hour: int = 12) -> float:
    return datetime(2026, 10, day, hour).timestamp()


class FriendshipPolicyTests(unittest.TestCase):
    def test_first_useful_action_only_awards_friendship_once(self) -> None:
        relationship = PetState()
        start = stamp()
        relationship._credit_friendship("pet", start, 60.0)
        self.assertEqual(relationship.friendship, 16.0)
        relationship._credit_friendship("pet", start + 10, 50.0)
        self.assertEqual(relationship.friendship, 16.0)
        relationship._credit_friendship("pet", start + 13 * 60, 50.0)
        self.assertEqual(relationship.friendship, 17.0)

    def test_variety_bonus_requires_previous_useful_action(self) -> None:
        relationship = PetState()
        start = stamp()
        relationship._credit_friendship("feed", start, 60.0)
        relationship._credit_friendship("talk", start + 60, 70.0)
        self.assertAlmostEqual(relationship.friendship, 15 + 0.9 + 1.35)
        self.assertEqual(relationship.care_types_today, ["feed", "talk"])

    def test_no_rewards_for_full_need_or_energy_drinks(self) -> None:
        relationship = PetState()
        for action, need in (("pet", 81), ("energy_drink", 0), ("sleep", 0)):
            relationship._credit_friendship(action, stamp(), need)
        self.assertEqual(relationship.friendship, 15)

    def test_daily_cap_and_next_day_reset(self) -> None:
        relationship = PetState()
        first = stamp()
        for number in range(20):
            relationship._credit_friendship("pet", first + 800 * number, 0)
        self.assertEqual(relationship.friendship_gained_today, FRIENDSHIP_DAILY_CAP)
        relationship._credit_friendship("talk", stamp(13), 0)
        self.assertGreater(relationship.friendship, 15 + FRIENDSHIP_DAILY_CAP)

    def test_invalid_and_backward_times_never_award(self) -> None:
        record = PetState()
        record._credit_friendship("talk", float("nan"), 0)
        record._credit_friendship("talk", 0, 0)
        self.assertEqual(record.friendship, 15)
        start = stamp()
        record._credit_friendship("talk", start, 0)
        record._credit_friendship("talk", start - 100, 0)
        self.assertEqual(record.friendship, 16)

    def test_pet_state_serialized_relationship_is_unchanged(self) -> None:
        state = PetState(updated_at=stamp())
        state.interact("pet", now=stamp())
        serialized = encode_pet_state(state)
        restored = decode_pet_state(serialized, now=stamp())
        self.assertEqual(serialized, encode_pet_state(restored))
        self.assertEqual(clamp_saved_time(None), 0.0)


if __name__ == "__main__":
    unittest.main()
