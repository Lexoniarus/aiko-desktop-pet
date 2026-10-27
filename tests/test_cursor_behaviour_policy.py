"""Temporal cursor decisions with controlled local evidence."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.cursor_attention import CursorPerception
from aiko_pet.pet.mind.cursor_behaviour import (
    CursorBehaviourContext,
    CursorBehaviourPolicy,
)


class CursorBehaviourPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = CursorBehaviourPolicy()
        self.context = CursorBehaviourContext(2, 80, 70)

    def decide(self, now=10.0, **values):
        p = CursorPerception(sampled_at=now, distance=0.6, side=1, valid=True)
        return self.policy.evaluate(replace(p, **values), self.context, now)

    def test_calm_reachable_pointer_requires_wait(self):
        self.assertEqual(
            self.decide(reachable=True, stationary_seconds=1).reaction, "observe"
        )
        intent = self.decide(reachable=True, stationary_seconds=4)
        self.assertEqual(intent.reaction, "approach")
        again = self.decide(10.1, reachable=True, stationary_seconds=4.1)
        self.assertEqual(again.token, intent.token)

    def test_speed_distance_direction_are_combined(self):
        for fields in [
            dict(distance=5, speed=8, closing_speed=8),
            dict(distance=0.2, speed=8, closing_speed=-8),
            dict(distance=0.2, speed=0.2, closing_speed=0.2),
        ]:
            self.assertNotIn(self.decide(**fields).reaction, ("flee", "avoid"))
        self.assertEqual(self.decide(speed=8, closing_speed=8).reaction, "flee")

    def test_trust_and_energy_bound_startle_and_retreat(self):
        self.context = replace(self.context, friendship_level=10)
        self.assertEqual(self.decide(speed=8, closing_speed=8).reaction, "avoid")
        self.policy.reset()
        self.context = replace(self.context, energy=5)
        self.assertEqual(self.decide(speed=8, closing_speed=8).reaction, "startle")

    def test_completion_and_hectic_repeats_have_recovery(self):
        first = self.decide(speed=8, closing_speed=8)
        self.policy.note_motion_finished(first.token, 10.5)
        self.assertEqual(
            self.decide(10.6, speed=8, closing_speed=8).reaction, "observe"
        )
        self.assertEqual(
            self.decide(11, reachable=True, stationary_seconds=5).reaction, "observe"
        )

    def test_stale_and_unreachable_samples_cannot_approach(self):
        self.assertEqual(self.decide(stationary_seconds=10).reaction, "ignore")
        self.assertEqual(self.decide(sampled_at=0).reaction, "ignore")

    def test_motion_ends_without_unbounded_following(self):
        intent = self.decide(reachable=True, stationary_seconds=4)
        self.policy.note_motion_finished(intent.token, 11)
        self.assertFalse(self.decide(12, reachable=True, stationary_seconds=6).moving)

    def test_expired_approach_starts_pause_without_completion_callback(self):
        first = self.decide(reachable=True, stationary_seconds=4)
        self.assertTrue(first.moving)
        expired = self.decide(first.until + 0.1, reachable=True, stationary_seconds=7)
        self.assertFalse(expired.moving)
        self.assertGreater(self.policy.recover_until, first.until + 10)
        self.assertFalse(self.decide(14, reachable=True, stationary_seconds=8).moving)
