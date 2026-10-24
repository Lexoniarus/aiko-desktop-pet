"""Deterministic care-period qualification, without wall waits or native UI."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.pet.care_evidence import CareActivity, CareExperience
from aiko_pet.pet.care_experiences import record_experience
from aiko_pet.pet.friendship_history import CriticalBucket, FriendshipHistory
from aiko_pet.pet.long_term_moodlets import advance_long_term, prepare_long_term
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletGroup,
    MoodletId,
    MoodletOutcome,
    MoodletState,
)
from aiko_pet.pet.wishes import WishArea, WishTargetKind

HOUR = 3600
DAY = 24 * HOUR
HISTORY = FriendshipHistory(baseline=0)


def contact(receipt, at, activity=CareActivity.SOCIAL, *, wish=None, win=False):
    area, kind, target = {
        CareActivity.SOCIAL: (WishArea.SOCIAL, WishTargetKind.SOCIAL, "chat"),
        CareActivity.PETTING: (WishArea.AFFECTION, WishTargetKind.CARE, "pet"),
        CareActivity.PLAY: (WishArea.GAMES, WishTargetKind.GAME, "mastermind"),
    }[activity]
    return CareExperience(
        receipt,
        at,
        activity,
        MoodletOutcome.WIN if win else MoodletOutcome.COMPLETED,
        area,
        kind,
        target,
        wish_instance_id=wish,
        pleasant=True,
    )


def upsetting(receipt, at, *, violation=True):
    return CareExperience(
        receipt,
        at,
        CareActivity.POKING,
        MoodletOutcome.COMPLETED,
        upsetting=True,
        boundary_violated=violation,
    )


def evaluate(events, *, history=HISTORY):
    state = prepare_long_term(MoodletState(), elapsed=0)
    for event in events:
        state = advance_long_term(
            state, history, elapsed=event.occurred_at, sleeping=False
        )
        state, _ = record_experience(state, event)
    return advance_long_term(state, history, elapsed=DAY, sleeping=False)


def families(state):
    return {
        e.definition_id
        for e in state.active
        if MOODLET_CATALOG.definitions[e.definition_id].group == MoodletGroup.LONG_TERM
    }


class LongTermMoodletTests(unittest.TestCase):
    def test_sleep_across_period_boundary_preserves_unaccounted_awake_gap(self):
        state = prepare_long_term(MoodletState(), elapsed=0)
        state = advance_long_term(state, HISTORY, elapsed=4 * HOUR, sleeping=False)
        state = advance_long_term(state, HISTORY, elapsed=DAY, sleeping=True)
        self.assertNotIn(MoodletId.OVERLOOKED, families(state))
        state = advance_long_term(
            state, HISTORY, elapsed=DAY + 4 * HOUR, sleeping=False
        )
        state = advance_long_term(state, HISTORY, elapsed=2 * DAY, sleeping=True)
        self.assertIn(MoodletId.OVERLOOKED, families(state))
        state = advance_long_term(state, HISTORY, elapsed=3 * DAY, sleeping=True)
        self.assertEqual(
            next(
                e for e in state.active if e.definition_id == MoodletId.OVERLOOKED
            ).level,
            1,
        )

    def test_continuous_good_contact_does_not_slide_one_encounter_forever(self):
        events = tuple(
            contact(
                str(n), n * HOUR, CareActivity.SOCIAL if n % 2 else CareActivity.PETTING
            )
            for n in range(10)
        )
        self.assertIn(MoodletId.TRUSTING, families(evaluate(events)))

    def test_overflow_starts_unknown_history_instead_of_forgetting_a_boundary(self):
        state = prepare_long_term(MoodletState(), elapsed=0)
        state, _ = record_experience(state, upsetting("bad", 0))
        for n in range(512):
            state, _ = record_experience(state, contact(str(n), n + 1))
        self.assertEqual(state.care_evidence.baseline, 512)
        self.assertFalse(state.care_evidence.progress)
        state = prepare_long_term(state, elapsed=512)
        self.assertEqual(state.care_evidence.progress[0].period_start, 512)
        self.assertEqual(decode_moodlets(encode_moodlets(state), elapsed=512), state)

    def test_current_and_longest_awake_gaps_survive_old_and_new_storage(self):
        state = prepare_long_term(MoodletState(), elapsed=0)
        state = advance_long_term(state, HISTORY, elapsed=9 * HOUR, sleeping=False)
        state, _ = record_experience(state, contact("late", 9 * HOUR))
        self.assertEqual(
            decode_moodlets(encode_moodlets(state), elapsed=9 * HOUR), state
        )
        raw = encode_moodlets(state)
        for cursor in raw["care_evidence"]["progress"]:
            cursor.pop("longest_awake_contact_gap_seconds")
        legacy = decode_moodlets(raw, elapsed=9 * HOUR)
        self.assertTrue(
            all(
                p.longest_awake_contact_gap_seconds == 0
                for p in legacy.care_evidence.progress
            )
        )

    def test_good_distributed_day_qualifies_three_distinct_patterns_once(self):
        events = (
            contact("a", 0, wish=1),
            contact("b", 4 * HOUR, CareActivity.PETTING, wish=2),
            contact("c", 8 * HOUR, CareActivity.PLAY, wish=3, win=True),
        )
        state = evaluate(events)
        self.assertEqual(
            families(state),
            {
                MoodletId.TRUSTING,
                MoodletId.APPRECIATED,
                MoodletId.OPTIMISTIC,
            },
        )
        repeated = advance_long_term(state, HISTORY, elapsed=DAY, sleeping=False)
        self.assertEqual(repeated, state)
        self.assertTrue(all(e.level == 1 for e in state.active))
        cause = next(
            e for e in state.active if e.definition_id == MoodletId.TRUSTING
        ).causes[0]
        self.assertEqual(cause.period.encounters, 3)
        self.assertEqual(cause.period.fulfilled_wishes, 3)
        self.assertEqual(decode_moodlets(encode_moodlets(state), elapsed=DAY), state)

    def test_repeated_actions_in_one_visit_cannot_manufacture_patterns(self):
        events = tuple(
            contact(str(n), n * 60, CareActivity.PLAY, wish=n + 1, win=True)
            for n in range(5)
        )
        state = evaluate(events)
        self.assertNotIn(MoodletId.TRUSTING, families(state))
        self.assertNotIn(MoodletId.APPRECIATED, families(state))
        self.assertNotIn(MoodletId.OPTIMISTIC, families(state))

    def test_trust_rejects_real_deficient_exposure_and_communicated_disregard(self):
        events = (
            contact("a", 0),
            contact("b", 4 * HOUR, CareActivity.PETTING),
            contact("c", 8 * HOUR),
        )
        poor = replace(
            HISTORY,
            critical=(
                CriticalBucket(
                    0,
                    (7200, 0, 0, 0, 0),
                    width=7200,
                ),
            ),
        )
        self.assertNotIn(MoodletId.TRUSTING, families(evaluate(events, history=poor)))
        state = evaluate((*events, upsetting("bad", 10 * HOUR)))
        self.assertNotIn(MoodletId.TRUSTING, families(state))

    def test_uncertainty_requires_distinct_pleasant_then_upsetting_pairs(self):
        events = (
            contact("a", 0),
            upsetting("bad-a", HOUR),
            contact("b", 4 * HOUR),
            upsetting("bad-b", 5 * HOUR),
        )
        self.assertIn(MoodletId.UNCERTAIN, families(evaluate(events)))
        self.assertNotIn(
            MoodletId.UNCERTAIN,
            families(
                evaluate((
                    events[0],
                    events[1],
                    events[3],
                ))
            ),
        )
        self.assertNotIn(
            MoodletId.UNCERTAIN,
            families(
                evaluate((
                    events[0],
                    upsetting("a", HOUR),
                    contact("b", HOUR + 1),
                    upsetting("b", HOUR + 2),
                ))
            ),
        )

    def test_guarded_requires_three_independent_incidents_spanning_four_hours(self):
        events = tuple(upsetting(str(n), (1 + 2 * n) * HOUR) for n in range(3))
        self.assertIn(MoodletId.GUARDED, families(evaluate(events)))
        state = prepare_long_term(MoodletState(), elapsed=0)
        for at in (HOUR, 3 * HOUR, 5 * HOUR):
            state, _ = record_experience(state, upsetting("same-incident", at))
        state = advance_long_term(state, HISTORY, elapsed=DAY, sleeping=False)
        self.assertNotIn(MoodletId.GUARDED, families(state))

    def test_sleep_pauses_awake_gap_without_erasing_time_before_sleep(self):
        state = prepare_long_term(MoodletState(), elapsed=0)
        for at, sleep in (
            (4 * HOUR, False),
            (12 * HOUR, True),
            (16 * HOUR, False),
            (DAY, True),
        ):
            state = advance_long_term(state, HISTORY, elapsed=at, sleeping=sleep)
        self.assertEqual(families(state), {MoodletId.OVERLOOKED})
        self.assertEqual(
            state.active[0].causes[0].period.awake_contact_gap_seconds, 8 * HOUR
        )
        state = prepare_long_term(MoodletState(), elapsed=0)
        state = advance_long_term(state, HISTORY, elapsed=DAY, sleeping=True)
        self.assertFalse(state.active)

    def test_contact_resets_current_gap_but_preserves_longest_gap_in_period(self):
        state = prepare_long_term(MoodletState(), elapsed=0)
        state = advance_long_term(state, HISTORY, elapsed=9 * HOUR, sleeping=False)
        state, _ = record_experience(state, contact("late", 9 * HOUR))
        state = advance_long_term(state, HISTORY, elapsed=DAY, sleeping=True)
        self.assertIn(MoodletId.OVERLOOKED, families(state))
        self.assertEqual(
            state.active[0].causes[0].period.awake_contact_gap_seconds, 9 * HOUR
        )
        self.assertNotIn(
            MoodletId.OVERLOOKED,
            families(
                evaluate((
                    contact("morning", 0),
                    contact("evening", 16 * HOUR),
                ))
            ),
        )

    def test_legacy_load_does_not_create_prior_care_periods(self):
        state = prepare_long_term(MoodletState(), elapsed=10 * DAY)
        state = advance_long_term(
            state, HISTORY, elapsed=10 * DAY + HOUR, sleeping=False
        )
        self.assertFalse(state.active)
        self.assertEqual(state.care_evidence.baseline, 10 * DAY)


if __name__ == "__main__":
    unittest.main()
