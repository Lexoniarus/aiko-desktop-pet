"""Fixed care-pattern stages and their smaller, separately signed contributions."""

import copy
import unittest

from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.pet.emotions import derive_emotional_state
from aiko_pet.pet.friendship_decay import balance_friendship, emotional_friendship_rates
from aiko_pet.pet.friendship_history import FriendshipHistory
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletContributions,
    MoodletEpisode,
    MoodletGroup,
    MoodletId,
    MoodletState,
    advance_moodlets,
    calculate_moodlet_contributions,
    reinforce_moodlet,
)
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState

DEFINITIONS = MOODLET_CATALOG.definitions
POLICY = MOODLET_CATALOG.long_term_policy
HEALTHY = NeedLevels(80, 80, 80, 80, 80)


def age(state, seconds, at=0):
    return advance_moodlets(
        state,
        seconds,
        elapsed=at,
        before=HEALTHY,
        after=HEALTHY,
        definitions=DEFINITIONS,
        observed=False,
    )


def trigger(state, key, at=0):
    return reinforce_moodlet(state, key, elapsed=at, definitions=DEFINITIONS)


def long_term_state():
    return MoodletState(
        active=tuple(
            MoodletEpisode(i, d.id, 3, 0, 0, d.decay_stage_seconds)
            for i, d in enumerate(DEFINITIONS.values(), 1)
            if d.group == MoodletGroup.LONG_TERM
        )
    )


class LongTermMoodletTimingTests(unittest.TestCase):
    def test_all_six_families_reset_only_the_current_fixed_stage_without_banked_time(
        self,
    ):
        for key in (
            MoodletId.TRUSTING,
            MoodletId.APPRECIATED,
            MoodletId.OPTIMISTIC,
            MoodletId.UNCERTAIN,
            MoodletId.OVERLOOKED,
            MoodletId.GUARDED,
        ):
            duration = DEFINITIONS[key].decay_stage_seconds
            state = trigger(MoodletState(), key)
            for day, level in ((1, 2), (2, 3), (3, 3)):
                state = age(state, 86400, (day - 1) * 86400)
                state = trigger(state, key, day * 86400)
                self.assertEqual(state.active[0].level, level)
                self.assertEqual(state.active[0].remaining_seconds, duration)
                self.assertEqual(state.active[0].lower_stage_seconds, ())
            state = decode_moodlets(encode_moodlets(state), 3 * 86400)
            self.assertEqual(age(state, duration, 3 * 86400).active[0].level, 2)
            self.assertFalse(age(state, duration * 3, 3 * 86400).active)
            with self.assertRaises(ValueError):
                reinforce_moodlet(
                    state, key, elapsed=3 * 86400, definitions=DEFINITIONS, level=2
                )
        self.assertFalse(age(MoodletState(), 10**8).active)

    def test_joint_caps_keep_positive_and_negative_long_term_feelings_separate(self):
        state = long_term_state()
        contributions = calculate_moodlet_contributions(
            state,
            definitions=DEFINITIONS,
            long_term_policy=POLICY,
        )
        self.assertEqual(contributions, MoodletContributions(5, -10))
        emotional = derive_emotional_state(80, state.active, definitions=DEFINITIONS)
        self.assertEqual(
            (emotional.positive_intensity, emotional.negative_intensity), (9, 9)
        )
        for key in (MoodletId.SECURE, MoodletId.WITHHELD, MoodletId.FOOD_MONOTONY):
            state = MoodletState(
                active=(
                    *state.active,
                    MoodletEpisode(len(state.active) + 100, key, 3, 0, 0, 1200),
                )
            )
        self.assertEqual(
            calculate_moodlet_contributions(
                state,
                definitions=DEFINITIONS,
                long_term_policy=POLICY,
            ),
            MoodletContributions(20, -30),
        )

    def test_long_term_friendship_rates_replace_ordinary_rates_without_affecting_them(
        self,
    ):
        state = long_term_state()
        positive, negative = emotional_friendship_rates(
            50, 50, state, recent_contact=False
        )
        self.assertAlmostEqual(positive * 2880, 1.296)
        self.assertAlmostEqual(negative * 2880, 2.592)
        state = MoodletState(
            active=(
                *state.active,
                MoodletEpisode(100, MoodletId.SECURE, 1, 0, 0, 3600),
                MoodletEpisode(101, MoodletId.POKING, 1, 0, 0, 1200),
            )
        )
        actual = emotional_friendship_rates(50, 50, state, recent_contact=False)
        self.assertAlmostEqual(actual[0], positive + 0.003)
        self.assertAlmostEqual(actual[1], negative + 0.006)

    def test_expiry_inside_a_status_interval_stops_the_reduced_rate_at_that_boundary(
        self,
    ):
        wall = 1800000000
        pet = PetState(
            satiety=100,
            energy=100,
            fun=100,
            social=100,
            affection=100,
            mood=50,
            friendship=50,
            updated_at=wall,
            relationship=FriendshipHistory(
                baseline=0, continuous_since=0, last_contact=0
            ),
            moodlets=MoodletState(
                0, 2, (MoodletEpisode(1, MoodletId.TRUSTING, 1, 0, 0, 5),)
            ),
        )
        split = copy.deepcopy(pet)
        pet.advance(wall + 15, observed=False)
        split.advance(wall + 5, observed=False)
        split.advance(wall + 15, observed=False)
        self.assertEqual(pet.capture_checkpoint(), split.capture_checkpoint())
        expected = balance_friendship(50, positive=0.00005 * 5 / 30, negative=0)
        self.assertAlmostEqual(pet.friendship, expected, places=10)
        self.assertFalse(pet.moodlets.active)
