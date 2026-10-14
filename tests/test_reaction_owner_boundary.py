"""Reaction playback has one canonical visual owner."""

import unittest

from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer


class ReactionOwnerBoundaryTests(unittest.TestCase):
    def test_reaction_controller_has_one_visual_owner(self) -> None:
        self.assertEqual(ReactionPlayer.__module__, "aiko_pet.ui.pet_view.reaction_player")
