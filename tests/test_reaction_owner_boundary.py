"""Reaction playback has one canonical visual owner."""

import unittest

from aiko_pet.presentation.reaction_playback import (
    ReactionPlayer as LegacyPlayer,
)
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer


class ReactionOwnerBoundaryTests(unittest.TestCase):
    def test_import_identity(self) -> None:
        self.assertIs(ReactionPlayer, LegacyPlayer)
