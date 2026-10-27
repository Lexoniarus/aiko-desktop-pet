"""Controlled encounter timelines, no animation or wall-clock dependency."""

import unittest
from dataclasses import replace

from aiko_pet.pet.interaction_events import CursorWarningReceipt
from aiko_pet.pet.mind.cursor_attention import CursorPerception
from aiko_pet.pet.mind.cursor_behaviour import (
    CursorBehaviourContext,
    CursorBehaviourPolicy,
)


class CursorBehaviourPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = CursorBehaviourPolicy(session_id="fixture")
        self.context = CursorBehaviourContext(2, 80, 70)

    def decide(self, now=10.0, **values):
        p = CursorPerception(
            sampled_at=now, pointer=(400, 194), distance=0.6, side=1, valid=True
        )
        return self.policy.evaluate(replace(p, **values), self.context, now)

    def warned_threat(self, now=10.0):
        first = self.decide(now, speed=8, closing_speed=8)
        self.assertIsNone(first.experience)
        assert first.warning is not None
        self.policy.note_warning(CursorWarningReceipt(
            first.warning.warning_id, now, True,
        ))
        self.decide(now + .1, speed=2, closing_speed=-2)
        return self.decide(now + .2, speed=8, closing_speed=8)

    def interest_until(self, seconds, **fields):
        result = self.decide()
        for n in range(round(seconds * 10) + 1):
            result = self.decide(10 + n / 10, speed=2, **fields)
        return result

    def test_attention_precedes_selected_gaze_and_tracks_one_encounter(self):
        self.assertFalse(self.decide().gaze)
        for n in range(1, 12):
            intent = self.decide(10 + n / 10, speed=2)
        self.assertFalse(intent.gaze)
        intent = self.decide(11.2, speed=2, pointer=(500, 100))
        self.assertTrue(intent.gaze)
        self.assertAlmostEqual(intent.attention, 21.6)
        token = intent.token
        intent = self.decide(11.3, speed=2, pointer=(510, 100))
        self.assertEqual((intent.token, intent.target), (token, (510, 100)))

    def test_attention_is_time_based_at_different_tick_rates(self):
        for hz in (10, 30, 60):
            self.policy.reset()
            self.decide(0, speed=2)
            for n in range(1, 3 * hz + 1):
                result = self.decide(n / hz, speed=2)
            self.assertAlmostEqual(result.attention, 54)
            self.assertEqual(result.stage, 2)

    def test_far_cap_and_smooth_release(self):
        self.decide(0, speed=4, distance=5)
        for n in range(1, 101):
            result = self.decide(n / 10, speed=4, distance=5)
        self.assertEqual(result.attention, 25)
        self.assertEqual(result.stage, 1)
        for n in range(101, 131):
            result = self.decide(n / 10, stationary_seconds=1, distance=5)
        self.assertEqual((result.attention, result.stage), (0, 0))

    def test_duplicate_stale_and_gap_do_not_accumulate(self):
        self.decide(10, speed=2)
        first = self.decide(11, speed=2)
        duplicate = self.decide(11, speed=4)
        self.assertEqual(duplicate.attention, first.attention)
        self.decide(20, speed=4)
        self.assertEqual(self.policy.attention, first.attention)
        self.assertFalse(self.decide(21, sampled_at=10).gaze)
        self.decide(22, speed=4)
        self.assertEqual(self.policy.attention, first.attention)

    def test_held_side_turns_and_opposite_returns_through_front(self):
        self.decide(0, speed=2)
        for n in range(1, 41):
            result = self.decide(n / 10, speed=2)
        self.assertEqual((result.body, result.side), ("three_quarter", 1))
        for n in range(41, 46):
            result = self.decide(n / 10, speed=2, side=-1)
        self.assertEqual(result.side, 1)
        for n in range(46, 56):
            result = self.decide(n / 10, speed=2, side=-1)
        self.assertEqual(result.body, "front")
        for n in range(56, 74):
            result = self.decide(n / 10, speed=2, side=-1)
        self.assertEqual((result.body, result.side), ("three_quarter", -1))

    def test_high_attention_with_alternating_sides_keeps_body_front(self):
        self.decide(0, speed=4)
        for n in range(1, 101):
            result = self.decide(n / 10, speed=4, side=1 if n % 2 else -1)
            self.assertEqual(result.body, "front")
        self.assertEqual((result.attention, result.stage), (100, 3))

    def test_body_releases_after_far_hold_and_activity_clears_side_history(self):
        self.decide(0, speed=2)
        for n in range(1, 41):
            self.decide(n / 10, speed=2)
        self.assertEqual(self.decide(4.1, speed=2, distance=4).side, 1)
        for n in range(42, 52):
            result = self.decide(n / 10, speed=2, distance=4)
        self.assertEqual(result.body, "front")
        self.policy.suspend(5.2)
        self.assertEqual(self.policy.attention, 0)
        self.assertEqual(self.decide(5.3, speed=4).body, "front")

    def test_speed_distance_direction_are_combined(self):
        for fields in (
            dict(distance=5, speed=8, closing_speed=8),
            dict(distance=0.2, speed=8, closing_speed=-8),
            dict(distance=0.2, speed=0.2, closing_speed=0.2),
        ):
            self.assertFalse(self.decide(**fields).moving)
        self.policy.reset()
        self.assertEqual(self.warned_threat().reaction, "flee")

    def test_trust_and_state_change_strength_without_unlocking_feelings(self):
        for trust, expected in ((1, "flee"), (10, "avoid")):
            self.policy = CursorBehaviourPolicy(session_id="fixture")
            self.context = replace(self.context, friendship_level=trust)
            fear = self.warned_threat()
            self.assertEqual(fear.reaction, expected)
            assert fear.experience is not None
            self.assertEqual(fear.experience.feeling, "fear")
            self.policy.reset()
            self.assertIsNotNone(self.interest_until(5.9).experience)
        self.policy.reset()
        self.policy = CursorBehaviourPolicy(session_id="exhausted")
        self.context = replace(self.context, energy=5)
        self.assertEqual(self.warned_threat().reaction, "startle")

    def test_one_retreat_until_confirmed_exit_and_five_seconds_standing(self):
        first = self.warned_threat()
        self.policy.note_motion_finished(first.token, 10.5)
        for t in (11, 12, 15, 20):
            self.assertFalse(self.decide(t, speed=8, closing_speed=8).moving)
        self.decide(21, distance=5)
        self.decide(22, distance=5)
        self.assertTrue(self.warned_threat(23).moving)

    def test_hectic_sides_only_look_briefly_without_body_chasing(self):
        result = self.decide()
        for n in range(50):
            result = self.decide(10 + n * 0.1, side=1 if n % 2 else -1, speed=1)
            self.assertEqual(result.body, "front")
            self.assertFalse(result.moving)
            self.assertIsNone(result.experience)
        self.assertEqual(result.reaction, "ignore")

    def test_sampling_gap_invalidates_calm_without_rearming_escape(self):
        self.interest_until(2)
        self.assertEqual(self.decide(20, reachable=True).body, "front")
        self.assertFalse(self.decide(21, sampled_at=0).gaze)
        self.assertFalse(self.decide(22, reachable=True).moving)

    def test_completed_attempt_pauses_and_old_receipts_do_not_repeat(self):
        first = self.interest_until(6, reachable=True)
        self.policy.note_motion_finished(first.token, 16)
        for n in range(1, 100):
            result = self.decide(16 + n / 10, reachable=True)
            self.assertFalse(result.moving)
            self.assertIsNone(result.experience)
        self.assertGreaterEqual(self.policy.recover_until, 28)

    def test_invalid_far_and_high_pointer_cannot_approach(self):
        self.assertFalse(self.decide(sampled_at=0).gaze)
        self.assertFalse(self.interest_until(6, reachable=False).moving)

    def test_resting_pointer_never_qualifies_and_breaks_positive_duration(self):
        for n in range(100):
            self.decide(10 + n / 10, stationary_seconds=2)
        self.assertEqual(self.policy._curiosity_level, 0)
        self.policy.reset()
        self.interest_until(5)
        self.decide(15.1, stationary_seconds=.5)
        for n in range(1, 20):
            self.assertIsNone(self.decide(15.1 + n / 10, speed=2).experience)
        self.assertEqual(self.policy._curiosity_level, 0)

    def test_context_mood_does_not_generate_new_evidence_without_new_stimulus(self):
        self.interest_until(6)
        self.context = replace(self.context, friendship_level=10, mood=100)
        self.assertIsNone(self.decide(16.1).experience)
