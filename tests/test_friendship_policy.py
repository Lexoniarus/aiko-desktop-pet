"""Rolling care credit, durable contact and progressive daily friendship paths."""

import unittest

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.friendship import calculate_friendship_reward
from aiko_pet.pet.friendship_decay import advance_friendship, passive_friendship
from aiko_pet.pet.friendship_history import FriendshipHistory, FriendshipProgress
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.state import PetState

START = 1_800_000_000.
HEALTHY = (100.,) * 5


def reward(progress, action="pet", need=0):
    record = PetState(friendship=progress.points, relationship=progress.history,
                      lived_seconds=progress.elapsed, updated_at=START)
    result = calculate_friendship_reward(record, action, START + progress.elapsed, need)
    assert result is not None
    return result


def healthy_time(progress, seconds):
    return advance_friendship(progress, seconds, HEALTHY, HEALTHY, sleeping=False)


class FriendshipPolicyTests(unittest.TestCase):
    def fresh(self, points=15):
        return FriendshipProgress(points, FriendshipHistory(baseline=0), 0)

    def test_shared_short_cap_and_no_variety_bonus(self):
        first = reward(self.fresh(), "feed")
        second = reward(first, "talk")
        self.assertEqual(first.points, 15.75)
        self.assertEqual(second.points, first.points)
        self.assertEqual(sum(e.amount for e in second.history.rewards), .75)

    def test_repetitions_leave_anchor_eligible_empty_attempts_set_it(self):
        value = reward(self.fresh())
        value = reward(healthy_time(value, 7100))
        self.assertEqual(dict(value.history.eligible)["pet"], 0)
        value = reward(healthy_time(value, 100))
        self.assertEqual(value.points, 16.5)
        value = reward(healthy_time(value, 7200), "energy_drink")
        value = reward(value, "talk")
        value = reward(value, "feed")
        self.assertEqual(dict(value.history.eligible)["feed"], value.elapsed)
        self.assertEqual(value.history.last_contact, value.elapsed)

    def test_high_need_reduction_and_energy_drink_credit(self):
        for action, need, expected in (("pet", 81, .25), ("pet", 80, .75),
                                       ("feed", 81, .225), ("energy_drink", 0, .25),
                                       ("energy_drink", 81, .0625)):
            with self.subTest(action=action, need=need):
                self.assertAlmostEqual(reward(self.fresh(), action, need).points - 15,
                                       expected)

    def test_rolling_day_does_not_reset_at_midnight(self):
        value = self.fresh()
        for index in range(8):
            value = reward(value)
            if index != 7:
                value = healthy_time(value, 7200)
        self.assertAlmostEqual(sum(e.amount for e in value.history.rewards), 5)
        before = value.points
        value = reward(healthy_time(value, 7200), "talk")
        self.assertEqual(value.points, before)
        self.assertEqual(value.history.last_contact, value.elapsed)
        value = reward(healthy_time(value, 8 * 3600))
        self.assertAlmostEqual(value.history.rewards[-1].amount, .75)
        self.assertLessEqual(sum(e.amount for e in value.history.rewards), 5)

    def test_full_points_still_record_contact_without_budget_credit(self):
        value = reward(self.fresh(100))
        self.assertEqual(value.points, 100)
        self.assertEqual(value.history.rewards, ())
        self.assertEqual(value.history.last_contact, 0)

    def test_invalid_times_and_sleep_create_no_contact(self):
        pet = PetState(updated_at=START)
        for stamp in (0, -1, float("nan"), float("inf")):
            self.assertIsNone(calculate_friendship_reward(pet, "talk", stamp, 0))
        self.assertIsNone(calculate_friendship_reward(pet, "sleep", START, 0))
        self.assertIsNone(pet.friendship_history.last_contact)

    def test_contact_requires_personal_intake_or_accepted_care(self):
        pet = PetState(satiety=50, energy=50, updated_at=START)
        pet.consume_item("onigiri", ConsumptionOrigin.AUTONOMOUS, now=START)
        self.assertIsNone(pet.friendship_history.last_contact)
        pet.consume_item("energy_drink", ConsumptionOrigin.HANDOVER, now=START)
        self.assertEqual(pet.friendship_history.last_contact, 0)
        self.assertAlmostEqual(pet.friendship, 15.25)
        refused = PetState(satiety=100, energy=100, updated_at=START)
        for action in ("feed", "energy_drink", "play", "sleep"):
            refused.interact(action, now=START)
        self.assertIsNone(refused.friendship_history.last_contact)

    def test_one_completed_round_is_contact_two_are_rewarded(self):
        for units, gain in ((0, 0), (1, 0), (2, .75)):
            pet = PetState(fun=20, updated_at=START)
            pet.record_game_experience(GameExperience("rock_paper_scissors", units),
                                       now=START)
            self.assertAlmostEqual(pet.friendship, 15 + gain)
            self.assertEqual(pet.friendship_history.last_contact,
                             None if units == 0 else 0)

    def test_factor_crossings_are_independent_of_advance_partition(self):
        whole = passive_friendship(95, 52)
        split = 95
        for _ in range(520):
            split = passive_friendship(split, .1)
        self.assertAlmostEqual(whole, split, places=9)
        self.assertEqual(passive_friendship(1, 10000), 0)
        self.assertEqual(passive_friendship(0, 100), 0)

    def test_absence_grace_and_whole_gap(self):
        for hours, reference in ((4, 0), (8, 2), (12, 4), (24, 16),
                                 (48, 52), (72, 100)):
            with self.subTest(hours=hours):
                result = healthy_time(self.fresh(95), hours * 3600)
                self.assertAlmostEqual(result.points, passive_friendship(95, reference))

    def test_latest_two_through_eight_visit_daily_ranges(self):
        cases = (
            ((0, 2.5, 5, 7.5, 10, 12, 14, 16), (96, 100)),
            ((0, 3, 6, 9, 12, 16), (96, 100)),
            ((0, 4, 8, 12, 16), (86.1, 90)),
            ((0, 6, 12, 16), (69.1, 70.9)),
            ((0, 8, 16), (50.8, 51.7)),
            ((0, 16), (34.1, 35.5)),
        )
        for visits, (expected_low, expected_high) in cases:
            with self.subTest(visits=len(visits)):
                value = self.fresh(95)
                low, high = 100., 0.
                for day in range(540):
                    for hour in visits:
                        target = (day * 24 + hour) * 3600
                        value = healthy_time(value, target - value.elapsed)
                        if day == 539:
                            low = min(low, value.points)
                        value = reward(value)
                        if day == 539:
                            high = max(high, value.points)
                    value = healthy_time(value, (day + 1) * 86400 - value.elapsed)
                    if day == 539:
                        low = min(low, value.points)
                self.assertGreaterEqual(low, expected_low)
                self.assertLessEqual(high, expected_high + 1e-8)

    def test_roundtrip_preserves_contact_rewards_and_negative_caps(self):
        pet = PetState(updated_at=START, affection=25)
        pet.interact("pet", now=START)
        pet.apply_relationship_penalty("click", .25)
        raw = encode_pet_state(pet)
        restored = decode_pet_state(raw, now=START + 3600)
        self.assertEqual(encode_pet_state(restored), raw)
        restored.interact("pet", now=START)
        self.assertEqual(restored.friendship, pet.friendship)
        self.assertEqual(restored.friendship_history.rewards,
                         pet.friendship_history.rewards)

    def test_wall_rebase_does_not_refund_elapsed_limits(self):
        pet = PetState(updated_at=START, affection=20)
        pet.interact("pet", now=START)
        pet.advance(START - 86400, elapsed_seconds=3600)
        pet.interact("pet", now=START - 86400)
        self.assertEqual(pet.friendship, 15.75)
        self.assertEqual(pet.friendship_history.last_contact, 3600)
        self.assertEqual(dict(pet.friendship_history.eligible)["pet"], 0)

    def test_negative_caps_survive_restart_and_are_not_progressively_scaled(self):
        for points in (10, 95):
            pet = PetState(friendship=points, updated_at=START)
            for _ in range(8):
                pet.apply_relationship_penalty("click", .25)
            self.assertEqual(pet.friendship, points - 1)
            pet = decode_pet_state(encode_pet_state(pet), now=START)
            self.assertEqual(pet.apply_relationship_penalty("click", .25), 0)
            pet.advance(START + 60)
            self.assertEqual(pet.apply_relationship_penalty("click", .25), .25)
            self.assertIsNone(pet.friendship_history.last_contact)

    def test_legacy_migration_invents_no_absence_or_critical_history(self):
        pet = decode_pet_state(
            dict(friendship=80, satiety=0, updated_at=START), now=START,
        )
        self.assertIsNone(pet.friendship_history.baseline)
        pet.advance(START + 3 * 86400)
        self.assertEqual(pet.friendship, 80)
        self.assertEqual(pet.friendship_history.baseline, 3 * 86400)
        self.assertIsNone(pet.friendship_history.last_contact)
        self.assertEqual(pet.friendship_history.critical, ())
        reloaded = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        reloaded.advance(pet.updated_at + 8 * 3600)
        self.assertLess(reloaded.friendship, pet.friendship)
