"""Idle emote choice is pet-owned and preserves its historic import."""

import unittest

from aiko_pet.pet.animation.idle_emote import choose_idle_emote
from aiko_pet.presentation.reaction_playback import (
    choose_idle_emote as legacy_choose_idle_emote,
)


class IdleEmoteBoundaryTests(unittest.TestCase):
    def test_legacy_import_has_one_owner(self) -> None:
        self.assertIs(choose_idle_emote, legacy_choose_idle_emote)

    def test_need_priority(self) -> None:
        self.assertEqual(
            choose_idle_emote(energy=0, satiety=0, mood=0, affection=0),
            "sleeps",
        )
        self.assertEqual(
            choose_idle_emote(energy=75, satiety=75, mood=90, affection=75),
            "star",
        )
