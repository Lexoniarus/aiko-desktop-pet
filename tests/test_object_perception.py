"""Recognition depends on continuous evidence, not update frequency."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_perception import (
    ItemPresentation,
    ObjectCandidate,
    ObjectPerception,
)

APPLE = ObjectCandidate("one", "apple", "food", 100, 0, True)
INSPECTED = replace(APPLE, resting=False, inspecting=True)


class ObjectPerceptionTests(unittest.TestCase):
    def sample(self, step: float):
        sensor = ObjectPerception()
        result = ()
        for index in range(round(1 / step) + 1):
            result = sensor.observe((INSPECTED,), now=index * step, x=0, height=0,
                                    width=192, attentive=True)
        return result

    def test_identity_is_hidden_until_recognized(self):
        sensor = ObjectPerception()
        for now in (0, 0.2):
            result = sensor.observe((INSPECTED,), now=now, x=0, height=0, width=192,
                                    attentive=True)
        self.assertIsNone(result[0].identity)
        result = sensor.observe((INSPECTED,), now=0.6, x=0, height=0, width=192,
                                attentive=True)
        self.assertEqual(result[0].identity, "apple")

    def test_ground_and_moving_items_are_not_identified_from_proximity(self):
        for resting in (True, False):
            sensor = ObjectPerception()
            for now in (0, .3, 1, 2):
                seen = sensor.observe((replace(APPLE, resting=resting),), now=now,
                                      x=0, height=0, width=192, attentive=True)
            self.assertEqual(len(seen), 1)
            self.assertIsNone(seen[0].identity)
            self.assertIsNone(seen[0].kind)

    def test_presentation_needs_a_continuous_hold_and_survives_face_to_hand_move(self):
        sensor = ObjectPerception()

        def sample(now, x, gesture="gesture", attentive=True):
            return sensor.observe((replace(
                APPLE, resting=False, presentation=ItemPresentation(gesture, x, 0),
            ),), now=now, x=0, height=0, width=192, attentive=attentive)

        for now, x in ((0, 0), (.4, .02), (.5, .8), (.7, 0), (1.1, .03)):
            seen = sample(now, x)
        self.assertIsNone(seen[0].identity)
        seen = sample(1.7, .01)
        self.assertEqual(seen[0].identity, "apple")
        self.assertTrue(seen[0].presented)
        self.assertTrue(sample(1.8, 1)[0].presented)
        self.assertFalse(sample(1.9, 0, "new_gesture")[0].presented)
        sample(2, 0, attentive=False)
        self.assertEqual(sample(3, 0), ())

    def test_moving_past_the_face_cannot_accumulate_stationary_presentation(self):
        sensor = ObjectPerception()
        for now, x in ((0, -.3), (.4, -.1), (.8, .1), (1.2, .3)):
            seen = sensor.observe((replace(
                APPLE, resting=False, presentation=ItemPresentation("gesture", x, 0),
            ),), now=now, x=0, height=0, width=192, attentive=True)
        self.assertFalse(seen[0].presented)
        self.assertIsNone(seen[0].identity)

    def test_same_duration_produces_same_knowledge_at_different_rates(self):
        self.assertEqual(self.sample(0.1), self.sample(0.25))

    def test_no_attention_or_out_of_range_supplies_no_knowledge(self):
        sensor = ObjectPerception()
        for attentive, x in ((False, 0), (True, 2000)):
            for now in (0, 1):
                self.assertEqual(sensor.observe((APPLE,), now=now, x=x, height=0,
                                                 width=192, attentive=attentive), ())

    def test_return_after_absence_does_not_count_unseen_time(self):
        sensor = ObjectPerception()
        for now, items in ((0, (APPLE,)), (1, ()), (100, (APPLE,))):
            result = sensor.observe(items, now=now, x=0, height=0, width=192,
                                    attentive=True)
        self.assertEqual(result, ())
