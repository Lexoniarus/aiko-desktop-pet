"""Qualified positive events spend, floor and extend actual bounded stage budgets."""

import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.pet.balance import BALANCE, parse_balance
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlet_timing import stage_seconds
from aiko_pet.pet.moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
    advance_moodlets,
    next_moodlet_boundary,
    reinforce_moodlet,
)
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState

DEFINITIONS = MOODLET_CATALOG.definitions
HEALTHY = NeedLevels(80, 80, 80, 80, 80)


def trigger(state, *, at=0, strength=1, key=MoodletId.PRIDE, cause=None):
    return reinforce_moodlet(
        state, key, elapsed=at, level=strength, cause=cause, definitions=DEFINITIONS
    )


def budgets(state):
    episode = state.active[0]
    return stage_seconds(episode, DEFINITIONS[episode.definition_id])


def age(state, seconds, *, at=0):
    return advance_moodlets(
        state,
        seconds,
        elapsed=at,
        before=HEALTHY,
        after=HEALTHY,
        definitions=DEFINITIONS,
        observed=False,
    )


class PositiveMoodletTimingTests(unittest.TestCase):
    def test_ascent_restores_base_floors_and_preserves_longer_lower_residuals(self):
        first = trigger(MoodletState())
        self.assertEqual(budgets(first), (3600,))
        second = trigger(age(first, 600), at=600)
        self.assertEqual(budgets(second), (3600, 2700))
        partial = replace(
            second,
            active=(
                replace(
                    second.active[0],
                    remaining_seconds=900,
                    lower_stage_seconds=(4200,),
                ),
            ),
        )
        third = trigger(partial, at=600)
        self.assertEqual(budgets(third), (4200, 2700, 2700))
        self.assertEqual(budgets(partial), (4200, 900))

    def test_two_tier_outcomes_choose_ascent_or_renewal_and_keep_one_real_cause(self):
        cause = MoodletCause(
            MoodletCauseKind.WISH_FULFILLED,
            0,
            "round:1",
            wish=MoodletWishCause(1, "win_overall", "blackjack", "total_wins", 3),
            target_id="blackjack",
            outcome=MoodletOutcome.WIN,
        )
        for prior, expected in (
            (0, (3600, 2700)),
            (1, (3600, 2700, 2700)),
            (2, (3600, 2700, 2700)),
            (3, (4200, 3300, 3300)),
        ):
            state = (
                MoodletState()
                if prior == 0
                else trigger(MoodletState(), strength=prior)
            )
            result = trigger(state, strength=2, cause=cause)
            self.assertEqual(budgets(result), expected)
            self.assertEqual(result.active[0].causes, (cause,))
            self.assertEqual(trigger(result, at=1, strength=2, cause=cause), result)

    def test_level_three_adds_ten_minutes_per_tier_up_to_the_joint_270_minutes(self):
        state = trigger(MoodletState(), strength=3)
        state = replace(
            state, active=(replace(state.active[0], remaining_seconds=1200),)
        )
        renewed = trigger(state)
        self.assertEqual(budgets(renewed), (4200, 3300, 1800))
        for at in range(1, 12):
            renewed = trigger(renewed, at=at)
        self.assertEqual(budgets(renewed), (5400, 5400, 5400))
        self.assertEqual(sum(budgets(renewed)), 270 * 60)

    def test_single_tier_food_extends_without_resetting_or_acquiring_other_stages(self):
        food = trigger(MoodletState(), key=MoodletId.FOOD_FULFILLED)
        self.assertEqual(budgets(food), (3600,))
        food = age(food, 2100)
        food = trigger(food, at=2100, key=MoodletId.FOOD_FULFILLED)
        self.assertEqual(budgets(food), (2100,))  # 25 minutes become 35 minutes.
        for at in range(2101, 2110):
            food = trigger(food, at=at, key=MoodletId.FOOD_FULFILLED)
        self.assertEqual(budgets(food), (5400,))
        ended = age(food, 5400, at=2109)
        fresh = trigger(ended, at=7509, key=MoodletId.FOOD_FULFILLED)
        self.assertEqual((fresh.active[0].instance_id, budgets(fresh)), (2, (3600,)))

    def test_actual_lower_budgets_survive_boundaries_reload_and_passive_reads(self):
        state = trigger(MoodletState(), strength=3)
        state = replace(
            state,
            active=(
                replace(
                    state.active[0],
                    remaining_seconds=200,
                    lower_stage_seconds=(4200, 3300),
                ),
            ),
        )
        pet = PetState(lived_seconds=0, moodlets=state)
        before = pet.capture_checkpoint()
        self.assertEqual(snapshot_pet(pet).moodlets[0].remaining_decay_seconds, 7700)
        self.assertEqual(pet.capture_checkpoint(), before)
        self.assertEqual(
            next_moodlet_boundary(state, elapsed=0, definitions=DEFINITIONS), 200
        )
        second = age(state, 200)
        self.assertEqual(budgets(second), (4200, 3300))
        second = decode_moodlets(encode_moodlets(second), 200)
        first = age(second, 3300, at=200)
        self.assertEqual(budgets(first), (4200,))
        self.assertFalse(age(first, 4200, at=3500).active)
        self.assertFalse(age(state, 10**8).active)

    def test_old_implicit_stages_are_preserved_until_an_actual_reinforcement(self):
        legacy = MoodletState(0, 2, (MoodletEpisode(1, MoodletId.PRIDE, 2, 0, 0, 100),))
        decoded = decode_moodlets(encode_moodlets(legacy), 0)
        self.assertEqual(budgets(decoded), (7200, 100))
        first = age(decoded, 100)
        self.assertEqual(budgets(first), (7200,))
        self.assertEqual(decode_moodlets(encode_moodlets(first), 100), first)
        self.assertEqual(budgets(trigger(decoded)), (5400, 2700, 2700))

    def test_balance_rejects_base_or_extension_above_the_shared_stage_cap(self):
        raw = load_json(
            Path(__file__).resolve().parents[1] / "aiko_pet/data/balance.json"
        )
        cap = BALANCE.integer("moodlets", "positive_stage_cap_seconds")
        for field in (
            "positive_level_one_seconds",
            "positive_upper_stage_seconds",
            "positive_renewal_seconds",
        ):
            broken = {**raw, "moodlets": {**raw["moodlets"], field: cap + 1}}
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_balance(broken)
