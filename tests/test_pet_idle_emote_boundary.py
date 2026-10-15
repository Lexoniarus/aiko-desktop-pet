"""Idle emote choice is pet-owned and preserves its historic import."""

import unittest

from aiko_pet.pet.animation.idle_emote import choose_idle_emote


class IdleEmoteBoundaryTests(unittest.TestCase):
    def test_emote_choice_has_one_pet_owner(self) -> None:
        self.assertEqual(
            choose_idle_emote.__module__, "aiko_pet.pet.animation.idle_emote"
        )

    def test_need_priority(self) -> None:
        self.assertEqual(
            choose_idle_emote(energy=0, satiety=0, mood=0, affection=0),
            "sleeps",
        )
        self.assertEqual(
            choose_idle_emote(energy=75, satiety=75, mood=90, affection=75),
            "star",
        )
