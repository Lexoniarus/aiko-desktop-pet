"""Mind and its catalogue have one canonical pet-owned identity."""

import unittest
from pathlib import Path

from aiko_pet.pet.mind import PetMind
from aiko_pet.pet.mind.cursor_attention import CursorAttention
from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook


class PetMindBoundaryTests(unittest.TestCase):
    def test_mind_and_catalogue_have_exact_canonical_owners(self) -> None:
        self.assertEqual(PetMind.__module__, "aiko_pet.pet.mind.mind")
        self.assertEqual(DialogueBook.__module__, "aiko_pet.pet.mind.catalog")

    def test_mind_owns_distinct_session_cursor_attention(self) -> None:
        first = PetMind()
        second = PetMind()
        self.assertIsInstance(first.cursor_attention, CursorAttention)
        self.assertIsNot(first.cursor_attention, second.cursor_attention)

    def test_catalogue_stays_in_shared_data_directory(self) -> None:
        root = Path(__file__).resolve().parents[1] / "aiko_pet"
        self.assertEqual(CATALOGUE, root / "data" / "dialogues.de.json")
        self.assertTrue(CATALOGUE.is_file())
