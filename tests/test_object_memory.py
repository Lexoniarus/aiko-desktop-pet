"""Lost sight preserves old location; knowledge expires by active time."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation


class ObjectMemoryTests(unittest.TestCase):
    def test_absence_does_not_reveal_a_new_location(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.update((), now=100)
        self.assertEqual(memory.snapshot(), (seen,))
        memory.update((), now=602)
        self.assertEqual(memory.snapshot(), ())

    def test_new_observed_location_retains_learned_identity(self):
        memory = ObjectMemory()
        seen = ObjectObservation("one", "apple", "food", 100, 0, True, 1)
        memory.update((seen,), now=1)
        memory.update((replace(seen, x=300, identity=None, kind=None,
                               observed_at=2),), now=2)
        self.assertEqual(memory.snapshot()[0].identity, "apple")
        self.assertEqual(memory.snapshot()[0].x, 300)
        memory.forget("one")
        self.assertEqual(memory.snapshot(), ())
