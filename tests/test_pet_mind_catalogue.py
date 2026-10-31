"""The pet mind uses the canonical packaged German dialogue catalogue."""

from __future__ import annotations

import unittest
from pathlib import Path

from aiko_pet.pet.mind import catalog

ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"


class PetMindCatalogueTests(unittest.TestCase):
    def test_dialogue_catalogue_path_points_to_packaged_index(self) -> None:
        self.assertEqual(
            catalog.CATALOGUE,
            ROOT / "data" / "dialogues" / "de" / "index.json",
        )
        self.assertTrue(catalog.CATALOGUE.is_file())
        book = catalog.DialogueBook.from_file()
        self.assertGreater(len(book.lines), 0)


if __name__ == "__main__":
    unittest.main()
