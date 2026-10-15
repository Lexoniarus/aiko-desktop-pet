"""Recognition depends on continuous evidence, not update frequency."""

import unittest

from aiko_pet.pet.mind.object_perception import ObjectCandidate, ObjectPerception

APPLE = ObjectCandidate("one", "apple", "food", 100, 0, True)


class ObjectPerceptionTests(unittest.TestCase):
    def sample(self, step: float):
        sensor = ObjectPerception()
        result = ()
        for index in range(round(1 / step) + 1):
            result = sensor.observe((APPLE,), now=index * step, x=0, height=0,
                                    width=192, attentive=True)
        return result

    def test_identity_is_hidden_until_recognized(self):
        sensor = ObjectPerception()
        for now in (0, 0.2):
            result = sensor.observe((APPLE,), now=now, x=0, height=0, width=192,
                                    attentive=True)
        self.assertIsNone(result[0].identity)
        result = sensor.observe((APPLE,), now=0.6, x=0, height=0, width=192,
                                attentive=True)
        self.assertEqual(result[0].identity, "apple")

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
