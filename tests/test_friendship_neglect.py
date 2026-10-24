"""Critical histories, per-interval overlap and recovery survive real elapsed time."""

import copy
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.application.storage_contracts import StorageError
from aiko_pet.infrastructure.friendship_codec import (
    decode_friendship,
    encode_friendship,
    valid_friendship,
)
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.friendship_decay import advance_friendship, passive_friendship
from aiko_pet.pet.friendship_history import FriendshipHistory, FriendshipProgress
from aiko_pet.pet.state import PetState

START = 1_800_000_000.
HEALTHY = (100.,) * 5


def period(value, hours, needs, *, contact=True, sleeping=False):
    for _ in range(round(hours * 240)):
        if contact:
            value = replace(value, history=replace(value.history,
                                                   last_contact=value.elapsed))
        value = advance_friendship(value, 15, needs, needs, sleeping=sleeping)
    return value


class FriendshipNeglectTests(unittest.TestCase):
    def fresh(self):
        return FriendshipProgress(100, FriendshipHistory(baseline=0), 0)

    def test_critical_and_zero_allowances_are_not_retroactive(self):
        for hours, need, reference in ((.75, 20, 0), (3, 20, .25),
                                       (2, 0, .5), (8, 0, 4.5)):
            with self.subTest(hours=hours, need=need):
                result = period(self.fresh(), hours, (need, 100, 100, 100, 100))
                self.assertAlmostEqual(result.points,
                                       passive_friendship(100, reference), places=7)

    def test_multiple_needs_use_the_strongest_rate_not_the_sum(self):
        one = period(self.fresh(), 8, (0, 100, 100, 100, 100))
        five = period(self.fresh(), 8, (0,) * 5)
        self.assertAlmostEqual(one.points, five.points)

    def test_absence_and_neglect_max_is_chosen_per_interval(self):
        # Nonzero critical: 2h grace, .25/h until 6h, .5/h thereafter.
        # Absence dominates after 4h: .5/h. The union costs 2.5 reference
        # points, rather than sum=4 or max(total,total)=2.
        value = period(self.fresh(), 8, (20, 100, 100, 100, 100), contact=False)
        self.assertAlmostEqual(value.points, passive_friendship(100, 2.5), places=7)

    def test_disjoint_critical_periods_accumulate_refilling_stops_current_charge(self):
        value = period(self.fresh(), 1.5, (20, 100, 100, 100, 100))
        value = period(value, 1, HEALTHY)
        self.assertEqual(value.points, 100)
        value = period(value, 1.5, (20, 100, 100, 100, 100))
        self.assertAlmostEqual(value.points, 99.5, places=7)
        recovered = period(value, 1, HEALTHY)
        self.assertEqual(recovered.points, value.points)
        self.assertTrue(recovered.history.critical)

    def test_exposure_expires_by_elapsed_time_without_reset_on_contact(self):
        value = period(self.fresh(), 1.5, (20, 100, 100, 100, 100))
        value = period(value, 24, HEALTHY)
        self.assertEqual(value.history.critical, ())
        value = period(value, 1.5, (20, 100, 100, 100, 100))
        self.assertEqual(value.points, 100)

    def test_restorative_sleep_exempts_energy_only_and_retains_old_history(self):
        value = period(self.fresh(), 3, (100, 10, 100, 100, 100))
        before = value.points
        asleep = advance_friendship(value, 3600, (100, 10, 100, 100, 100),
                                    (100, 20, 100, 100, 100), sleeping=True)
        self.assertEqual(asleep.points, before)
        self.assertTrue(asleep.history.critical)
        hunger = period(self.fresh(), 3, (0, 100, 100, 100, 100), sleeping=True)
        self.assertLess(hunger.points, 100)

    def test_real_need_crossings_do_not_charge_previous_healthy_time(self):
        pet = PetState(updated_at=START, friendship=100, satiety=30, energy=100,
                       fun=100, social=100, affection=100)
        pet.advance(START + 2 * 3600)
        self.assertEqual(pet.friendship, 100)
        pet.advance(START + 3 * 3600)
        self.assertLess(pet.friendship, 100)

    def test_long_gaps_keep_bounded_history_and_reference_consistency(self):
        pet = PetState(updated_at=START, friendship=10, satiety=0, energy=0,
                       fun=0, social=0, affection=0)
        pet.advance(START + 3 * 86400)
        self.assertEqual(pet.friendship, 0)
        self.assertLessEqual(len(pet.friendship_history.critical), 1441)
        self.assertGreaterEqual(pet.friendship_history.critical[0].start,
                                pet.lived_seconds - 86460)
        raw = encode_pet_state(pet)
        self.assertEqual(
            encode_pet_state(decode_pet_state(raw, now=pet.updated_at)), raw,
        )

    def test_split_and_save_reopen_follow_the_same_critical_timeline(self):
        whole = PetState(updated_at=START, friendship=95, satiety=0, energy=100,
                         fun=100, social=100, affection=100)
        divided = copy.deepcopy(whole)
        whole.advance(START + 10 * 3600)
        for hour in range(1, 11):
            divided.advance(START + hour * 3600)
            divided = decode_pet_state(
                encode_pet_state(divided), now=divided.updated_at,
            )
        self.assertAlmostEqual(divided.friendship, whole.friendship, places=4)
        self.assertEqual(len(divided.friendship_history.critical),
                         len(whole.friendship_history.critical))
        for actual, expected in zip(divided.friendship_history.critical,
                                    whole.friendship_history.critical, strict=True):
            self.assertEqual(actual.start, expected.start)
            self.assertEqual(actual.width, expected.width)
            for first, last in ((actual.critical, expected.critical),
                                (actual.zero, expected.zero)):
                for a, b in zip(first, last, strict=True):
                    self.assertAlmostEqual(a, b, places=7)

    def test_invalid_histories_are_rejected_without_losing_pet_progress(self):
        raw = encode_friendship(self.fresh().history)
        for field, value in (("version", True), ("version", 2), ("baseline", -1),
                             ("last_contact", 1), ("rewards", [{}] * 66),
                             ("eligible", {"sleep": 0}), ("critical", [{}] * 1442)):
            broken = {**raw, field: value}
            self.assertFalse(valid_friendship(broken, 0), field)
            pet = decode_pet_state(dict(friendship=72, relationship=broken), now=START)
            self.assertEqual(pet.friendship, 72)
            self.assertIsNone(pet.friendship_history.baseline)
        self.assertEqual(decode_friendship(raw, 0), self.fresh().history)

    def test_future_relationship_record_stops_import_without_replacing_source(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            path.write_text('{"version":1,"pet":{"friendship":72,'
                            '"relationship":{"version":999}}}', encoding="utf-8")
            original = path.read_bytes()
            store = StateStore(path)
            with self.assertRaises(StorageError):
                store.load_session(now=START)
            self.assertFalse(store.path.exists())
            self.assertEqual(path.read_bytes(), original)

    def test_malformed_exposure_and_reward_evidence_is_rejected(self):
        valid = period(self.fresh(), 1, (0, 100, 100, 100, 100))
        original = encode_friendship(valid.history)
        for field, value in (("width", 0), ("width", float("nan")),
                             ("start", .5), ("critical", [0]),
                             ("zero", [4000, 0, 0, 0, 0])):
            raw = copy.deepcopy(original)
            raw["critical"][0][field] = value
            self.assertFalse(valid_friendship(raw, 3600), field)
        for records in (
            [dict(at=0, kind="pet", amount=1)],
            [dict(at=4000, kind="pet", amount=.25)],
            [dict(at=0, kind="sleep", amount=.25)],
        ):
            raw = {**original, "rewards": records}
            self.assertFalse(valid_friendship(raw, 3600))
