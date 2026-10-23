"""Real history qualifies after-effects; old handled burden cannot return."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.friendship_decay import advance_friendship
from aiko_pet.pet.friendship_history import FriendshipHistory, FriendshipProgress
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletId,
    MoodletState,
    advance_moodlets,
    calculate_moodlet_contributions,
)
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.poor_care import prepare_poor_care, qualify_poor_care
from aiko_pet.pet.state import PetState

DEFINITIONS = MOODLET_CATALOG.definitions
HEALTHY = NeedLevels(50, 50, 50, 50, 50)


class PoorCareMoodletTests(unittest.TestCase):
    def setUp(self):
        self.state = MoodletState()
        self.relationship = FriendshipProgress(50, FriendshipHistory(baseline=0), 0)

    def period(self, hours, needs, *, after=None, sleeping=False):
        """Feed fixed trajectories through the production history and policies."""
        after = needs if after is None else after
        start = self.relationship.elapsed
        self.state = prepare_poor_care(self.state, self.relationship.history,
                                      elapsed=start)
        self.relationship = advance_friendship(
            self.relationship, hours * 3600,
            tuple(getattr(needs, n) for n in needs.__dataclass_fields__),
            tuple(getattr(after, n) for n in after.__dataclass_fields__),
            sleeping=sleeping,
        )
        self.state = advance_moodlets(self.state, hours * 3600, elapsed=start,
                                      before=needs, after=after,
                                      definitions=DEFINITIONS)
        self.state = qualify_poor_care(
            self.state, self.relationship.history, elapsed=self.relationship.elapsed,
            before=needs, after=after, sleeping=sleeping, definitions=DEFINITIONS,
        )

    def episode(self, key=MoodletId.HUNGER_WORN):
        return next(e for e in self.state.active if e.definition_id == key)

    def test_critical_and_zero_routes_use_alternative_levels_and_never_add_them(self):
        for need, first in ((20, 2), (0, 1)):
            with self.subTest(need=need):
                self.setUp()
                low = replace(HEALTHY, satiety=need)
                self.period(first - .01, low)
                self.assertFalse(self.state.active)
                self.period(.01, low)
                self.assertEqual(self.episode().level, 1)
                self.period(first, low)
                self.assertEqual(self.episode().level, 2)
                self.period(first, low)
                self.assertEqual(self.episode().level, 3)
                triggered = self.episode().last_trigger_at
                self.period(first, low)
                self.assertEqual(self.episode().last_trigger_at, triggered)

    def test_unqualified_disjoint_burden_survives_stable_care_but_expires_at_24h(self):
        low = replace(HEALTHY, satiety=20)
        self.period(1, low)
        self.period(.5, HEALTHY)
        self.period(1, low)
        self.assertEqual(self.episode().level, 1)
        self.setUp()
        self.period(1, low)
        self.period(24, HEALTHY)
        self.period(1, low)
        self.assertFalse(self.state.active)

    def test_recovery_pause_requalification_and_retained_stage_progress(self):
        low = replace(HEALTHY, satiety=20)
        self.period(2, low)
        self.period(2, low)
        self.period(.5, HEALTHY)
        self.period(80 / 60, HEALTHY)
        self.assertAlmostEqual(self.episode().remaining_seconds, 2400)
        self.period(1, replace(HEALTHY, satiety=38))
        self.assertTrue(self.episode().decay_paused)
        self.assertAlmostEqual(self.episode().remaining_seconds, 2400)
        self.period(.5, HEALTHY)
        self.assertAlmostEqual(self.episode().remaining_seconds, 2400)
        self.period(40 / 60, HEALTHY)
        self.assertEqual(self.episode().level, 1)
        self.assertAlmostEqual(self.episode().remaining_seconds, 7200)

    def test_recovered_impression_needs_fresh_burden_despite_old_history(self):
        low = replace(HEALTHY, satiety=20)
        self.period(2, low)
        old_id = self.episode().instance_id
        self.period(2.5, HEALTHY)
        self.assertFalse(self.state.active)
        self.assertTrue(self.relationship.history.critical)
        self.period(.25, low)
        self.assertFalse(self.state.active)
        self.period(1.75, low)
        self.assertEqual(self.episode().level, 1)
        self.assertGreater(self.episode().instance_id, old_id)

    def test_only_genuinely_higher_fresh_burden_restarts_an_existing_stage(self):
        low = replace(HEALTHY, satiety=20)
        self.period(2, low)
        self.period(2, low)
        old_id = self.episode().instance_id
        self.period(.5, HEALTHY)
        self.period(1, HEALTHY)
        remaining = self.episode().remaining_seconds
        for hours in (.25, 1.75, 2):
            self.period(hours, low)
            self.assertEqual(self.episode().level, 2)
            self.assertEqual(self.episode().remaining_seconds, remaining)
        self.period(2, low)
        self.assertEqual(self.episode().instance_id, old_id)
        self.assertEqual(self.episode().level, 3)
        self.assertEqual(self.episode().remaining_seconds, 7200)

    def test_residual_new_burden_is_preserved_after_a_handled_threshold(self):
        low = replace(HEALTHY, satiety=20)
        self.period(2, low)
        self.period(1, low)  # Unhandled remainder after the first threshold.
        self.period(.5, HEALTHY)
        self.period(1, low)  # Remainder + this hour qualifies fresh level one.
        self.assertEqual(self.episode().level, 1)
        self.period(2.5, HEALTHY)
        self.assertFalse(self.state.active)
        self.period(.25, low)
        self.assertFalse(self.state.active)  # Fresh level one was already handled.

    def test_sleep_exempts_restoring_energy_only_and_group_has_one_shared_cap(self):
        low = NeedLevels(20, 10, 20, 20, 20)
        self.period(2, low, after=replace(low, energy=25), sleeping=True)
        self.assertEqual(len(self.state.active), 4)
        self.assertNotIn(MoodletId.EXHAUSTION_IRRITATED,
                         [e.definition_id for e in self.state.active])
        self.assertEqual(calculate_moodlet_contributions(
            self.state, definitions=DEFINITIONS,
            long_term_policy=MOODLET_CATALOG.long_term_policy,
        ).negative_points, -15)
        self.assertEqual(self.relationship.history.penalties, ())

    def test_missing_emotional_markers_start_after_legacy_history(self):
        low = replace(HEALTHY, satiety=20)
        self.period(3, low)
        self.state = MoodletState()  # Earlier save has care history, no new markers.
        self.period(.5, low)
        self.assertFalse(self.state.active)
        self.period(1.5, low)
        self.assertEqual(self.episode().started_at, 5 * 3600)

    def test_reload_preserves_handled_and_unhandled_burden_through_recovery(self):
        low = replace(HEALTHY, satiety=20)
        self.period(2, low)
        self.period(1, low)
        self.period(.5, HEALTHY)
        stored = PetState(moodlets=self.state, relationship=self.relationship.history,
                          friendship=self.relationship.points,
                          lived_seconds=self.relationship.elapsed)
        loaded = decode_pet_state(encode_pet_state(stored))
        self.assertEqual(loaded.moodlets, self.state)
        self.state = loaded.moodlets
        self.relationship = FriendshipProgress(loaded.friendship,
                                               loaded.friendship_history,
                                               loaded.lived_seconds)
        self.period(1, low)
        self.period(2.5, HEALTHY)
        self.assertFalse(self.state.active)
        self.period(.25, low)
        self.assertFalse(self.state.active)

    def test_disjoint_deficits_keep_escalating_until_recovery_actually_qualifies(self):
        low = replace(HEALTHY, satiety=20)
        self.period(2, low)
        self.period(1, replace(HEALTHY, satiety=30))
        self.period(2, low)
        self.assertEqual(self.episode().level, 2)
        self.period(.25, HEALTHY)  # Fifteen healthy minutes are not qualification.
        self.period(2, low)
        self.assertEqual(self.episode().level, 3)
