"""Game UI objects use one canonical implementation after migration."""

import unittest

from aiko_pet.ui.windows.rock_paper_scissors_sequence import RockPaperScissorsSequence
from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow


class GameWindowOwnershipTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        self.assertEqual(
            RockPaperScissorsSequence.__module__,
            "aiko_pet.ui.windows.rock_paper_scissors_sequence",
        )
        self.assertEqual(
            RockPaperScissorsWindow.__module__,
            "aiko_pet.ui.windows.rock_paper_scissors_window",
        )
