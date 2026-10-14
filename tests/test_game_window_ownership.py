"""Game UI objects use one canonical implementation after migration."""

import unittest

from aiko_pet.ui.windows.rock_paper_scissors_sequence import RockPaperScissorsSequence
from aiko_pet.presentation.rock_paper_scissors_sequence import (
    RockPaperScissorsSequence as LegacySequence,
)
from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow
from aiko_pet.ui.rock_paper_scissors_window import (
    RockPaperScissorsWindow as LegacyWindow,
)


class GameWindowOwnershipTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        self.assertIs(RockPaperScissorsSequence, LegacySequence)
        self.assertIs(RockPaperScissorsWindow, LegacyWindow)
