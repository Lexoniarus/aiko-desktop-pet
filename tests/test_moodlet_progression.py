"""Pure Moodlet timelines, with explicit time and semantic qualification."""

from __future__ import annotations

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletGameResult,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
    advance_moodlets,
    next_moodlet_boundary,
    reinforce_moodlet,
    relieve_moodlet,
    resolve_moodlet_cause,
)
from aiko_pet.pet.needs import NeedLevels

DEFINITIONS = MOODLET_CATALOG.definitions
HEALTHY = NeedLevels(80, 80, 80, 80, 80)


def trigger(
    state: MoodletState, key: MoodletId, at: float = 0, level: int = 1,
) -> MoodletState:
    return reinforce_moodlet(state, key, elapsed=at, level=level,
                             definitions=DEFINITIONS)


def age(state, seconds, at=0, before=HEALTHY, after=HEALTHY, observed=True):
    return advance_moodlets(state, seconds, elapsed=at, before=before, after=after,
                            observed=observed, definitions=DEFINITIONS)


def relieve(state, at, instance=1):
    return relieve_moodlet(state, instance, elapsed=at, definitions=DEFINITIONS)


class MoodletProgressionTests(unittest.TestCase):
    def test_real_wish_causes_stack_once_and_keep_only_three_original_results(self):
        state = MoodletState()
        for number, game in enumerate(("blackjack", "tic_tac_toe", "blackjack",
                                        "rock_paper_scissors"), 1):
            at = number * 10
            cause = MoodletCause(
                MoodletCauseKind.WISH_FULFILLED, at, "session:1",
                wish=MoodletWishCause(number, "win_overall", game, "total_wins", 3),
                target_id=game, outcome=MoodletOutcome.WIN,
                game=MoodletGameResult(MoodletOutcome.WIN, 5, 3, 1),
            )
            state = reinforce_moodlet(state, MoodletId.PRIDE, elapsed=at,
                                     definitions=DEFINITIONS, level=2, cause=cause)
            same = reinforce_moodlet(state, MoodletId.PRIDE, elapsed=at + 1,
                                     definitions=DEFINITIONS, level=2, cause=cause)
            self.assertEqual(same, state)  # Duplicate delivery cannot refresh a tier.
            state = decode_moodlets(encode_moodlets(state), at)
        self.assertEqual([c.wish.instance_id for c in state.active[0].causes if c.wish],
                         [2, 3, 4])
        self.assertEqual(state.active[0].level, 3)
        self.assertEqual(len(age(state, 7200, at=40).active[0].causes), 2)
        raw = encode_moodlets(state)
        raw["active"][0]["causes"][0]["game"]["wins"] = 6
        with self.assertRaises(ValueError):
            decode_moodlets(raw, 40)

    def test_relief_retains_latest_causes_up_to_current_level_and_rolls_at_three(self):
        state = MoodletState()
        for number in range(1, 31):
            cause = MoodletCause(
                MoodletCauseKind.WISH_FULFILLED, number, f"relief:{number}",
                wish=MoodletWishCause(number, "avoid_round_loss", "blackjack",
                                      "next_non_loss", 1),
                target_id="blackjack", outcome=MoodletOutcome.DRAW,
            )
            state = reinforce_moodlet(state, MoodletId.RELIEF, elapsed=number,
                                     definitions=DEFINITIONS, cause=cause)
            self.assertEqual(len(state.active[0].causes), min(number, 3))
            expected = [f"relief:{n}" for n in range(max(1, number - 2), number + 1)]
            self.assertEqual([c.event_id for c in state.active[0].causes], expected)
        self.assertEqual([c.event_id for c in state.active[0].causes],
                         ["relief:28", "relief:29", "relief:30"])
        state = decode_moodlets(encode_moodlets(state), 30)
        state = age(state, DEFINITIONS[MoodletId.RELIEF].decay_stage_seconds, at=30)
        self.assertEqual(state.active[0].level, 2)
        self.assertEqual([c.event_id for c in state.active[0].causes],
                         ["relief:29", "relief:30"])
        new = replace(state.active[0].causes[-1], occurred_at=40, event_id="relief:new",
                      wish=MoodletWishCause(31, "avoid_round_loss", "blackjack",
                                            "next_non_loss", 1))
        state = reinforce_moodlet(state, MoodletId.RELIEF, elapsed=40,
                                 definitions=DEFINITIONS, cause=new)
        self.assertEqual([c.event_id for c in state.active[0].causes],
                         ["relief:29", "relief:30", "relief:new"])

    def test_quiet_time_decays_three_two_one_without_replaying_a_long_gap(self):
        state = trigger(MoodletState(), MoodletId.DISRUPTED)
        state = trigger(trigger(state, MoodletId.DISRUPTED), MoodletId.DISRUPTED)
        original = state
        for seconds, level, remaining in ((1799, 3, 1), (1800, 2, 1800),
                                          (3600, 1, 1800)):
            episode = age(state, seconds).active[0]
            self.assertEqual((episode.level, episode.remaining_seconds),
                             (level, remaining))
        self.assertEqual(age(state, 5400).active, ())
        self.assertEqual(age(state, 10**9).active, ())
        self.assertEqual(state, original)

    def test_pokes_and_pet_boundary_escalate_only_after_three_more_events(self):
        for key in (MoodletId.POKING, MoodletId.CROWDED):
            state = trigger(MoodletState(), key)
            self.assertEqual(state.active[0].level, 1)
            for count, level in ((1, 1), (2, 1), (3, 2), (4, 2), (5, 2), (6, 3)):
                state = trigger(state, key, at=count)
                self.assertEqual(state.active[0].level, level)
            for count in range(7, 30):
                state = trigger(state, key, at=count)
            episode = state.active[0]
            self.assertEqual((episode.level, episode.remaining_seconds), (3, 1200))
            self.assertEqual(state.next_instance_id, 2)

    def test_fulfillment_stacks_by_its_strength_food_only_refreshes(self):
        state = trigger(MoodletState(), MoodletId.PRIDE, level=2)
        state = trigger(state, MoodletId.PRIDE, at=10, level=2)
        self.assertEqual((state.active[0].level, state.active[0].remaining_seconds),
                         (3, 7200))
        food = trigger(MoodletState(), MoodletId.FOOD_FULFILLED)
        food = trigger(age(food, 3600), MoodletId.FOOD_FULFILLED, at=3600)
        self.assertEqual((food.active[0].level, food.active[0].remaining_seconds),
                         (1, 7200))
        expired = age(state, 6 * 3600, at=10)
        renewed = trigger(expired, MoodletId.PRIDE, at=21610)
        self.assertEqual((renewed.active[0].instance_id, renewed.active[0].level),
                         (2, 1))

    def test_refresh_retains_used_levels_and_the_five_minute_quiet_gate(self):
        state = trigger(MoodletState(), MoodletId.POKING)
        self.assertEqual(relieve(age(state, 299), 299), age(state, 299))
        state = relieve(age(state, 300), 300)
        self.assertEqual((state.active[0].remaining_seconds,
                          state.active[0].relieved_levels), (600, (1,)))
        self.assertEqual(relieve(state, 300), state)
        state = trigger(state, MoodletId.POKING, at=300)
        self.assertEqual(state.active[0].relieved_levels, (1,))
        self.assertEqual(relieve(state, 300), state)

    def test_escalation_and_revisit_do_not_reset_an_episodes_used_allowance(self):
        state = trigger(MoodletState(), MoodletId.POKING)
        state = relieve(age(state, 300), 300)
        for at in (300, 301, 302):
            state = trigger(state, MoodletId.POKING, at=at)
        state = relieve(age(state, 300, at=302), 602)
        self.assertEqual(state.active[0].relieved_levels, (1, 2))
        returned = age(state, 600, at=602)
        self.assertEqual(returned.active[0].level, 1)
        self.assertEqual(relieve(returned, 1202), returned)
        restored = decode_moodlets(encode_moodlets(returned), 1202)
        self.assertEqual(relieve(restored, 1202), restored)

    def test_one_relief_ends_only_the_current_tier_and_discards_excess(self):
        state = MoodletState(0, 2, (
            MoodletEpisode(1, MoodletId.POKING, 3, 0, 0, 100),
        ))
        shortened = relieve(state, 1100)
        self.assertEqual((shortened.active[0].level,
                          shortened.active[0].remaining_seconds), (2, 1200))
        self.assertEqual(shortened.active[0].relieved_levels, (3,))
        self.assertEqual(relieve(shortened, 1100, instance=99), shortened)
        ended = age(shortened, 2400, at=1100)
        renewed = trigger(ended, MoodletId.POKING, at=3500)
        self.assertEqual(renewed.active[0].relieved_levels, ())
        self.assertEqual(renewed.active[0].instance_id, 2)

    def test_withholding_waits_for_resolution_but_unobserved_time_still_ages(self):
        state = trigger(MoodletState(), MoodletId.WITHHELD)
        self.assertEqual(age(state, 3600), state)
        self.assertEqual(relieve(state, 600), state)
        resolved = resolve_moodlet_cause(state, 1, definitions=DEFINITIONS)
        self.assertEqual(resolved.active[0].level, 1)
        self.assertEqual(age(resolved, 1200).active, ())
        self.assertEqual(age(state, 1200, observed=False).active, ())

    def test_poor_care_waits_thirty_minutes_and_preserves_paused_stage_progress(self):
        state = trigger(MoodletState(), MoodletId.HUNGER_WORN, level=2)
        state = age(state, 1800)
        self.assertEqual(state.active[0].remaining_seconds, 7200)
        self.assertFalse(state.active[0].decay_paused)
        state = age(state, 4800, at=1800)
        self.assertEqual(state.active[0].remaining_seconds, 2400)
        low = replace(HEALTHY, satiety=38)
        state = age(state, 600, at=6600, before=low, after=low)
        self.assertEqual(state.active[0].remaining_seconds, 2400)
        self.assertIsNone(state.active[0].recovery_since)
        state = age(state, 1800, at=7200)
        self.assertEqual(state.active[0].remaining_seconds, 2400)
        self.assertEqual(age(state, 2400, at=9000).active[0].level, 1)

    def test_recovery_crossing_uses_only_the_healthy_part_of_an_interval(self):
        state = trigger(MoodletState(), MoodletId.HUNGER_WORN)
        low, high = replace(HEALTHY, satiety=30), replace(HEALTHY, satiety=50)
        state = age(state, 3600, before=low, after=high)
        self.assertEqual(state.active[0].recovery_since, 1800)
        self.assertEqual(state.active[0].remaining_seconds, 7200)
        state = age(state, 3600, at=3600, before=high, after=low)
        self.assertEqual(state.active[0].remaining_seconds, 5400)
        self.assertIsNone(state.active[0].recovery_since)

    def test_poor_care_burden_is_absolute_and_relief_requires_stable_recovery(self):
        state = trigger(MoodletState(), MoodletId.HUNGER_WORN, level=2)
        self.assertEqual(trigger(state, MoodletId.HUNGER_WORN, at=1), state)
        self.assertEqual(relieve(state, 1800), state)
        ready = age(state, 1800)
        shortened = relieve(ready, 1800)
        self.assertEqual(shortened.active[0].remaining_seconds, 5400)
        stacked = trigger(shortened, MoodletId.HUNGER_WORN, at=1800, level=3)
        self.assertEqual(stacked.active[0].level, 3)
        self.assertEqual(stacked.active[0].relieved_levels, (2,))
        self.assertIsNone(stacked.active[0].recovery_since)
        exhaustion = age(trigger(MoodletState(), MoodletId.EXHAUSTION_IRRITATED), 1800)
        self.assertEqual(relieve(exhaustion, 1800), exhaustion)

    def test_next_boundary_distinguishes_quiet_qualification_and_paused_cause(self):
        state = trigger(MoodletState(), MoodletId.POKING)
        self.assertEqual(next_moodlet_boundary(state, elapsed=0,
                                               definitions=DEFINITIONS), 1200)
        state = age(trigger(MoodletState(), MoodletId.HUNGER_WORN), 0)
        self.assertEqual(next_moodlet_boundary(state, elapsed=0,
                                               definitions=DEFINITIONS), 1800)

    def test_invalid_strengths_times_and_stale_triggers_do_not_mutate_state(self):
        state = trigger(MoodletState(), MoodletId.POKING, at=50)
        for at, level in ((49, 1), (50, True), (50, 2), (float("nan"), 1)):
            with self.subTest(at=at, level=level), self.assertRaises(ValueError):
                trigger(state, MoodletId.POKING, at=at, level=level)
        self.assertEqual(state.active[0].level, 1)
