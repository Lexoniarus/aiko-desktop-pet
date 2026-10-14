"""Mind and its catalogue have one canonical pet-owned identity."""

import unittest
from pathlib import Path

from aiko_pet.pet.mind import PetMind
from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook
from aiko_pet.personality.mind import AikoMind
from aiko_pet.personality.catalog import DialogueBook as LegacyDialogueBook


class PetMindBoundaryTests(unittest.TestCase):
    def test_mind_and_catalogue_keep_existing_public_identity(self) -> None:
        self.assertIs(PetMind, AikoMind)
        self.assertIs(DialogueBook, LegacyDialogueBook)

    def test_catalogue_stays_in_shared_data_directory(self) -> None:
        root = Path(__file__).resolve().parents[1] / "aiko_pet"
        self.assertEqual(CATALOGUE, root / "data" / "dialogues.de.json")
        self.assertTrue(CATALOGUE.is_file())
