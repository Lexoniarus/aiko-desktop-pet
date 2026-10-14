"""A particular character catalogue is injected at composition time."""

import random
import unittest

from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind import PetMind
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState


class CharacterMindInjectionTests(unittest.TestCase):
    def test_default_aiko_catalogue_uses_the_same_rng(self) -> None:
        mind = make_aiko_mind(started_at=20.0)
        self.assertIs(mind.book.rng, mind.rng)
        self.assertGreater(len(mind.book.lines), 0)
        self.assertEqual(mind.last_contact, 20.0)

    def test_pet_mind_accepts_non_aiko_dialogue_book(self) -> None:
        line = Line(
            id="custom", event="greeting", text="Hallo aus einem anderen Pet",
            animation="idle", moods=(), periods=(), weekdays=(),
            weight=1, cooldown_seconds=0,
        )
        rng = random.Random(2)
        book = DialogueBook((line,), rng=rng)
        mind = PetMind(book=book, rng=rng)
        self.assertIs(mind.book, book)
        selected = mind.say_event(
            "greeting", PetState(), context_at(1_781_000_000.0), 100.0,
        )
        assert selected is not None
        self.assertEqual(selected.text, "Hallo aus einem anderen Pet")
