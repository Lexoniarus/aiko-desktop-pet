"""Regression tests for friendship policy and persisted value normalization."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import datetime

from aiko_pet.domain import (
    CARE_PRIMARY_NEED,
    FRIENDSHIP_DAILY_CAP,
    PetState,
    bounded,
    clamp_saved_time,
)
from aiko_pet.friendship import (
    CARE_PRIMARY_NEED as NEW_PRIMARY_NEED,
    FRIENDSHIP_DAILY_CAP as NEW_DAILY_CAP,
    award_friendship_for_care,
)
from aiko_pet.value_rules import bounded as normalized_need


@dataclass
class Relationship:
    friendship: float = 15.0
    friendship_day: str = ""
    friendship_gained_today: float = 0.0
    care_types_today: list[str] = field(default_factory=list)
    care_last_rewards: dict[str, float] = field(default_factory=dict)


def stamp(day: int = 12, hour: int = 12) -> float:
    return datetime(2026, 10, day, hour).timestamp()


class FriendshipPolicyTests(unittest.TestCase):
    def test_legacy_imports_are_identical(self) -> None:
        self.assertIs(CARE_PRIMARY_NEED, NEW_PRIMARY_NEED)
        self.assertEqual(FRIENDSHIP_DAILY_CAP, NEW_DAILY_CAP)
        self.assertIs(bounded, normalized_need)

    def test_first_useful_action_only_awards_friendship_once(self) -> None:
        relationship = Relationship()
        start = stamp()
        award_friendship_for_care(relationship, "pet", start, 60.0)
        self.assertEqual(relationship.friendship, 16.0)
        award_friendship_for_care(relationship, "pet", start + 10, 50.0)
        self.assertEqual(relationship.friendship, 16.0)
        award_friendship_for_care(relationship, "pet", start + 13 * 60, 50.0)
        self.assertEqual(relationship.friendship, 17.0)

    def test_variety_bonus_requires_previous_useful_action(self) -> None:
        relationship = Relationship()
        start = stamp()
        award_friendship_for_care(relationship, "feed", start, 60.0)
        award_friendship_for_care(relationship, "talk", start + 60, 70.0)
        self.assertAlmostEqual(relationship.friendship, 15 + 0.9 + 1.35)
        self.assertEqual(relationship.care_types_today, ["feed", "talk"])

    def test_no_rewards_for_full_need_or_energy_drinks(self) -> None:
        relationship = Relationship()
        for action, need in (("pet", 81), ("energy_drink", 0), ("sleep", 0)):
            award_friendship_for_care(relationship, action, stamp(), need)
        self.assertEqual(relationship.friendship, 15)

    def test_daily_cap_and_next_day_reset(self) -> None:
        relationship = Relationship()
        first = stamp()
        for number in range(20):
            award_friendship_for_care(relationship, "pet", first + 800 * number, 0)
        self.assertEqual(relationship.friendship_gained_today, FRIENDSHIP_DAILY_CAP)
        award_friendship_for_care(relationship, "talk", stamp(13), 0)
        self.assertGreater(relationship.friendship, 15 + FRIENDSHIP_DAILY_CAP)

    def test_invalid_and_backward_times_never_award(self) -> None:
        record = Relationship()
        award_friendship_for_care(record, "talk", float("nan"), 0)
        award_friendship_for_care(record, "talk", 0, 0)
        self.assertEqual(record.friendship, 15)
        start = stamp()
        award_friendship_for_care(record, "talk", start, 0)
        award_friendship_for_care(record, "talk", start - 100, 0)
        self.assertEqual(record.friendship, 16)

    def test_pet_state_serialized_relationship_is_unchanged(self) -> None:
        state = PetState(updated_at=stamp())
        state.interact("pet", now=stamp())
        serialized = state.to_dict()
        restored = PetState.from_dict(serialized, now=stamp())
        self.assertEqual(serialized, restored.to_dict())
        self.assertEqual(clamp_saved_time(None), 0.0)


if __name__ == "__main__":
    unittest.main()
