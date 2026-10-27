"""Controlled encounter timelines, no animation or wall-clock dependency."""

import unittest
from dataclasses import replace

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

    def calm_until(self, seconds, **fields):
        for n in range(round(seconds * 10) + 1):
            result = self.decide(10 + n / 10, **fields)
        return result

    def test_head_then_body_then_bounded_approach(self):
        self.assertEqual(self.decide().body, "front")
        first = self.calm_until(2.9, reachable=True)
        self.assertEqual((first.reaction, first.body), ("observe", "front"))
        turn = self.decide(13, reachable=True)
        self.assertEqual((turn.reaction, turn.body), ("observe", "three_quarter"))
        first = self.calm_until(4.6, reachable=True)
        self.assertEqual(
            (first.reaction, first.body, first.steps), ("approach", "profile", 1)
        )
        self.assertEqual(self.decide(14.7, reachable=True).token, first.token)

    def test_speed_distance_direction_are_combined(self):
        for fields in (
            dict(distance=5, speed=8, closing_speed=8),
            dict(distance=0.2, speed=8, closing_speed=-8),
            dict(distance=0.2, speed=0.2, closing_speed=0.2),
        ):
            self.assertFalse(self.decide(**fields).moving)
        self.assertEqual(self.decide(speed=8, closing_speed=8).reaction, "flee")

    def test_trust_and_state_change_strength_without_unlocking_feelings(self):
        for trust, expected in ((1, "flee"), (10, "avoid")):
            self.policy.reset()
            self.context = replace(self.context, friendship_level=trust)
            fear = self.decide(speed=8, closing_speed=8)
            self.assertEqual(fear.reaction, expected)
            self.assertEqual(fear.experience.feeling, "fear")
            self.policy.reset()
            self.assertIsNotNone(self.calm_until(1).experience)
        self.policy.reset()
        self.context = replace(self.context, energy=5)
        self.assertEqual(self.decide(speed=8, closing_speed=8).reaction, "startle")

    def test_one_retreat_until_confirmed_exit_and_five_seconds_standing(self):
        first = self.decide(speed=8, closing_speed=8)
        self.policy.note_motion_finished(first.token, 10.5)
        for t in (11, 12, 15, 20):
            self.assertFalse(self.decide(t, speed=8, closing_speed=8).moving)
        self.decide(21, distance=5)
        self.decide(22, distance=5)
        self.assertTrue(self.decide(23, speed=8, closing_speed=8).moving)

    def test_hectic_sides_only_look_briefly_without_body_chasing(self):
        for n in range(50):
            result = self.decide(10 + n * 0.1, side=1 if n % 2 else -1, speed=1)
            self.assertEqual(result.body, "front")
            self.assertFalse(result.moving)
            self.assertIsNone(result.experience)
        self.assertEqual(result.reaction, "ignore")

    def test_sampling_gap_invalidates_calm_without_rearming_escape(self):
        self.calm_until(2)
        self.assertEqual(self.decide(20, reachable=True).body, "front")
        self.assertFalse(self.decide(21, sampled_at=0).gaze)
        self.assertFalse(self.decide(22, reachable=True).moving)

    def test_completed_attempt_pauses_and_old_receipts_do_not_repeat(self):
        first = self.calm_until(4.6, reachable=True)
        self.policy.note_motion_finished(first.token, 15)
        for n in range(1, 100):
            result = self.decide(15 + n / 10, reachable=True)
            self.assertFalse(result.moving)
            self.assertIsNone(result.experience)
        self.assertGreaterEqual(self.policy.recover_until, 27)

    def test_invalid_far_and_high_pointer_cannot_approach(self):
        self.assertFalse(self.decide(sampled_at=0).gaze)
        self.assertFalse(self.calm_until(6, reachable=False).moving)

    def test_context_mood_does_not_generate_new_evidence_without_new_stimulus(self):
        self.calm_until(1)
        self.context = replace(self.context, friendship_level=10, mood=100)
        self.assertIsNone(self.decide(11.1).experience)
