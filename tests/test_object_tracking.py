"""Spatial continuity does not disclose objective instance identity."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_tracking import ObjectTracker
from aiko_pet.pet.mind.object_perception import ObjectCandidate


class ObjectTrackingTests(unittest.TestCase):
    def test_observed_take_follows_visible_motion_but_never_bridges_loss(self):
        tracker = ObjectTracker(maximum_gap=1)
        item = ObjectCandidate("world_a", "apple", "food", 100, 0, True)
        first = tracker.update((item,), now=0, maximum_distance=50)[0]
        self.assertTrue(tracker.follow_taken(item.token))
        moving = replace(item, x=900, height=500, resting=False)
        held = tracker.update((moving,), now=.2, maximum_distance=50)[0]
        self.assertEqual(held.token, first.token)
        tracker.update((), now=.3, maximum_distance=50)
        self.assertIsNone(tracker.following_instance)
        seen = tracker.update((moving,), now=.4, maximum_distance=50)[0]
        self.assertNotEqual(seen.token, first.token)

    def test_continuity_uses_space_even_when_the_technical_handle_changes(self):
        tracker = ObjectTracker(maximum_gap=1)
        item = ObjectCandidate("world_a", "apple", "food", 100, 0, True)
        first = tracker.update((item,), now=0, maximum_distance=50)[0]
        second = tracker.update((replace(item, token="world_b", x=110),),
                                now=.2, maximum_distance=50)[0]
        self.assertEqual(first.token, second.token)
        self.assertEqual(tracker.resolve(second.token), "world_b")

    def test_same_world_handle_does_not_bridge_an_unseen_move_or_jump(self):
        item = ObjectCandidate("world_a", "apple", "food", 100, 0, True)
        for lost in ("gap", "invisible", "jump"):
            with self.subTest(lost=lost):
                tracker = ObjectTracker(maximum_gap=1)
                first = tracker.update((item,), now=0, maximum_distance=50)[0]
                if lost == "invisible":
                    tracker.update((), now=.1, maximum_distance=50)
                    self.assertIsNone(tracker.resolve(first.token))
                found = tracker.update(
                    (replace(item, x=300 if lost == "jump" else 100),),
                    now=2 if lost == "gap" else .2, maximum_distance=50,
                )[0]
                self.assertNotEqual(first.token, found.token)

    def test_distinct_and_ambiguous_identical_sightings_do_not_share_a_track(self):
        tracker = ObjectTracker(maximum_gap=1)
        a = ObjectCandidate("a", "apple", "food", 100, 0, True)
        b = replace(a, token="b", x=200)
        first = tracker.update((a, b), now=0, maximum_distance=100)
        next_seen = tracker.update((replace(b, x=190), replace(a, x=110)),
                                   now=.2, maximum_distance=100)
        self.assertEqual([item.token for item in next_seen],
                         [first[1].token, first[0].token])
        ambiguous = tracker.update((replace(a, x=150),), now=.4,
                                   maximum_distance=100)[0]
        self.assertNotIn(ambiguous.token, {item.token for item in first})
