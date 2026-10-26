"""Book eligibility controls free curiosity without deleting learned knowledge."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.pet.mind.object_intentions import ObjectGoal
from aiko_pet.pet.mind.object_knowledge import (
    ObjectMemorySnapshot,
    SavedObjectKnowledge,
)
from aiko_pet.pet.state import PetState


class ReadableAutonomyTests(unittest.TestCase):
    def setUp(self):
        self.book = SavedObjectKnowledge(
            "memory_1", "horoscope_book", "book", 100, 0, True, 0,
            False, "interrupted", instance_id="object_1",
        )
        self.awareness = ObjectAwareness(ObjectMemorySnapshot((self.book,), 2))
        self.pet = PetState(satiety=50, energy=50)

    def choose(self, now: float = 0.0, **kwargs):
        return self.awareness.choose_goal(
            self.pet, x=100, now=now, blocked=False, **kwargs,
        )

    def test_completed_unassessed_book_never_becomes_free_curiosity_again(self):
        self.awareness.readable = lambda _book: False
        original = self.awareness.memory.snapshot()
        for now in (0, 5, 600, 1200):
            self.assertIsNone(self.choose(now))
        self.assertEqual(self.awareness.memory.snapshot(), original)
        self.assertEqual(self.awareness.memory.snapshot()[0].instance_id, "object_1")
        self.assertEqual(self.awareness.autonomous_records(), ())

    def test_partial_reading_is_still_eligible_and_stale_goal_is_released(self):
        self.awareness = ObjectAwareness(ObjectMemorySnapshot((replace(
            self.book, assessed=True,
        ),), 2))
        self.awareness.readable = lambda book: book == "object_1"
        goal = self.choose()
        assert goal is not None
        self.assertEqual(goal.token, "memory_1")
        self.awareness.readable = lambda _book: False
        self.assertIsNone(self.choose(.01, changed=False))
        self.assertIsNone(self.awareness.intentions.goal)

    def test_existing_physical_commitment_can_finish_closing_and_putdown(self):
        goal = ObjectGoal("memory_1", "horoscope_book", "book", 100, 0, 0)
        self.awareness.intentions.adopt(goal)
        self.awareness.readable = lambda _book: False
        self.assertEqual(self.choose(committed="memory_1"), goal)

    def test_read_book_does_not_hide_wanted_food(self):
        food = replace(self.book, token="memory_2", identity="apple", kind="food",
                       assessed=True, instance_id="object_2")
        self.awareness = ObjectAwareness(ObjectMemorySnapshot((self.book, food), 3))
        goal = self.choose()
        assert goal is not None
        self.assertEqual(goal.token, "memory_2")


if __name__ == "__main__":
    unittest.main()
