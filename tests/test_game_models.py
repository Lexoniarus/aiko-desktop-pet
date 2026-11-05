"""Masked card reads and bounded placement without desktop state writes."""

import unittest
from dataclasses import fields

from aiko_pet.games.blackjack import Blackjack
from aiko_pet.ui.view_models.game_models import (
    HandAnchor,
    place_hand,
    project_dealer_hand,
)


class GameModelTests(unittest.TestCase):
    def test_hand_projection_carries_no_hidden_card_or_total(self):
        game = Blackjack(shuffle_deck=lambda _deck: None)
        hand = project_dealer_hand(game.table)
        self.assertEqual(len(hand.cards), 2)
        self.assertIsNone(hand.cards[1])
        self.assertEqual([f.name for f in fields(hand)], ["cards"])
        game.stand()
        game.reveal_dealer()
        self.assertIsNotNone(project_dealer_hand(game.table).cards[1])

    def test_long_hands_at_both_scales_remain_inside_taskbar_bounds(self):
        for scale in (1, 2):
            for x in (-100, 1200):
                anchor = HandAnchor(x, 950, 192 * scale, 208 * scale,
                                    0, 0, 1280, 984, scale)
                layout = place_hand(11, anchor)
                self.assertGreaterEqual(layout.x, 0)
                self.assertGreaterEqual(layout.y, 0)
                self.assertLessEqual(layout.x + layout.width, 1280)
                self.assertLessEqual(layout.y + layout.height, 984)
                self.assertGreaterEqual(layout.step, 20 * scale)
