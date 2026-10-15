"""Mind and its catalogue have one canonical pet-owned identity."""

import unittest
from pathlib import Path

from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.cursor_attention import CursorAttention
from aiko_pet.pet.mind.catalog import CATALOGUE


class PetMindBoundaryTests(unittest.TestCase):
    def test_mind_owns_distinct_session_cursor_attention(self) -> None:
        first = make_aiko_mind(started_at=0.0)
        second = make_aiko_mind(started_at=0.0)
        self.assertIsInstance(first.cursor_attention, CursorAttention)
        self.assertIsNot(first.cursor_attention, second.cursor_attention)

    def test_catalogue_stays_in_shared_data_directory(self) -> None:
        root = Path(__file__).resolve().parents[1] / "aiko_pet"
        self.assertEqual(CATALOGUE, root / "data" / "dialogues.de.json")
        self.assertTrue(CATALOGUE.is_file())
