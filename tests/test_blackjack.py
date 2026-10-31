"""Blackjack variant, hidden information and completion without UI code."""

import unittest

from aiko_pet.games.blackjack import Blackjack, Phase, hand_total
from aiko_pet.games.playing_cards import STANDARD_DECK, Card


def arranged_game(*cards: Card) -> Blackjack:
    def arrange(deck):
        deck[:] = [c for c in STANDARD_DECK if c not in cards] + list(reversed(cards))
    return Blackjack(shuffle_deck=arrange)


def card(rank: str, suit: str = "clubs") -> Card:
    return Card(suit, rank.zfill(2) if rank.isdecimal() else rank)


class BlackjackTests(unittest.TestCase):
    def test_ace_totals(self):
        for ranks, expected in ((('A', 'A', '9'), 21), (('A', 'A', 'A', 'K'), 13),
                                (('A', '6'), 17), (('K', 'Q', '2'), 22)):
            self.assertEqual(hand_total(tuple(card(r) for r in ranks)), expected)

    def test_naturals_resolve_before_input_and_only_revealed_results_count(self):
        for player, dealer, result in (
            ((card('A'), card('K')), (card('9'), card('8')), 'win'),
            ((card('9'), card('8')), (card('A'), card('K')), 'loss'),
            ((card('A'), card('K')),
             (card('A', 'hearts'), card('K', 'hearts')), 'draw'),
        ):
            game = arranged_game(player[0], dealer[0], player[1], dealer[1])
            self.assertEqual(game.table.phase, Phase.RESULT)
            self.assertIsNone(game.table.dealer[1])
            self.assertIsNone(game.table.result)
            with self.assertRaises(ValueError):
                game.hit()
            with self.assertRaises(ValueError):
                game.settle()
            game.reveal_dealer()
            game.settle()
            self.assertEqual(game.table.result, result)
            self.assertEqual(game.score.games, 1)
            with self.assertRaises(ValueError):
                game.settle()

    def test_soft_17_stands_without_drawing_and_ties(self):
        game = arranged_game(card('10'), card('A'), card('7'), card('6'))
        with self.assertRaises(ValueError):
            game.reveal_dealer()
        game.stand()
        with self.assertRaises(ValueError):
            game.dealer_step()
        game.reveal_dealer()
        game.dealer_step()
        self.assertEqual(len(game.table.dealer), 2)
        game.settle()
        self.assertEqual(game.table.result, 'draw')

    def test_player_bust_finishes_without_dealer_draws(self):
        game = arranged_game(card('K'), card('2'), card('8'), card('3'), card('9'))
        game.hit()
        self.assertEqual(game.table.phase, Phase.RESULT)
        game.reveal_dealer()
        game.settle()
        self.assertEqual(game.score.losses, 1)
        self.assertEqual(len(game.table.dealer), 2)

    def test_dealer_draws_one_card_at_a_time_and_busts(self):
        game = arranged_game(
            card('10'), card('2'), card('8'), card('3'),
            card('10', 'hearts'), card('K'),
        )
        game.stand()
        game.reveal_dealer()
        game.dealer_step()
        self.assertEqual(game.table.phase, Phase.DEALER)
        self.assertEqual(len(game.table.dealer), 3)
        game.dealer_step()
        game.settle()
        self.assertEqual(game.score.wins, 1)
        all_cards = (*game.table.player, *game.table.dealer)
        self.assertEqual(len(all_cards), len(set(all_cards)))

    def test_later_21_auto_stands_reset_shuffles_and_cancel_never_counts(self):
        game = arranged_game(card('10'), card('9'), card('5'), card('7'), card('6'))
        game.hit()
        self.assertEqual(game.table.phase, Phase.DEALER)
        game.reveal_dealer()
        while game.table.phase is Phase.DEALER:
            game.dealer_step()
        game.settle()
        game.next_round()
        self.assertIsNone(game.table.dealer[1])
        self.assertEqual(game.score.games, 1)
        game.cancel()
        with self.assertRaises(ValueError):
            game.hit()
        self.assertEqual(game.score.games, 1)

    def test_invalid_shuffle_and_unfinished_reset_are_rejected(self):
        with self.assertRaises(ValueError):
            Blackjack(shuffle_deck=lambda deck: deck.clear())
        with self.assertRaises(ValueError):
            Blackjack().next_round()
