"""Reveal/settlement ordering and cancellation using an injected clock."""

import unittest

from test_blackjack import arranged_game, card

from aiko_pet.games.blackjack import Phase
from aiko_pet.ui.windows.blackjack_sequence import BlackjackSequence


class BlackjackSequenceTests(unittest.TestCase):
    def make_flow(self, game):
        self.tasks = {}
        self.hands = []
        self.views = []
        self.lines = []
        self.delays = []
        self.rounds = []

        def schedule(delay, callback):
            self.delays.append(delay)
            self.tasks['turn'] = callback
            return 'turn'

        flow = BlackjackSequence(
            schedule=schedule, cancel=lambda token: self.tasks.pop(token, None),
            present=lambda table, score: self.views.append((table, score)),
            hand=lambda view, flip: self.hands.append((view, flip)),
            say=lambda line, _ms: self.lines.append(line), animate=lambda _name: None,
            dialogue=lambda event: event, game=game,
            round_event=self.rounds.append,
        )
        flow.greet()
        return flow

    def test_natural_reveals_then_settles_and_closing_after_result_keeps_unit(self):
        flow = self.make_flow(arranged_game(card('A'), card('8'), card('K'), card('9')))
        self.assertIsNone(self.hands[-1][0].cards[1])
        self.assertEqual(flow.game.score.games, 0)
        flow.advance()
        self.assertTrue(self.hands[-1][1])
        self.assertEqual(flow.game.score.games, 0)
        flow.advance()
        self.assertEqual(self.views[-1][0].result, 'win')
        self.assertEqual([e.outcome for e in self.rounds], [None, 'win'])
        self.assertEqual(self.rounds[0].identity, self.rounds[1].identity)
        self.assertEqual(flow.close().wins, 1)
        self.assertEqual(flow.close().games, 1)
        self.assertEqual(self.hands[-1][0].cards, ())

    def test_close_during_flip_never_counts_or_revives_hand(self):
        flow = self.make_flow(arranged_game(card('A'), card('8'), card('K'), card('9')))
        flow.advance()
        stale = self.tasks['turn']
        self.assertEqual(flow.close().games, 0)
        stale()
        self.assertEqual(self.tasks, {})
        self.assertEqual(self.hands[-1][0].cards, ())

    def test_player_bust_reveals_but_dealer_does_not_draw(self):
        flow = self.make_flow(arranged_game(
            card('10'), card('2'), card('8'), card('3'), card('9'),
        ))
        flow.hit()
        flow.hit()
        flow.advance()
        flow.advance()
        self.assertEqual(len(self.hands[-1][0].cards), 2)
        self.assertEqual(flow.game.score.losses, 1)
        self.assertIsNotNone(flow.pending_timer)
        self.tasks['turn']()
        self.assertIsNone(self.hands[-1][0].cards[1])

    def test_result_pause_then_auto_restart_preserves_score_and_blocks_input(self):
        flow = self.make_flow(arranged_game(
            card('10'), card('9'), card('8'), card('7'), card('K'),
        ))
        flow.stand()
        flow.advance()
        flow.advance()
        result = flow.game.table
        self.assertEqual(result.result, 'win')
        self.assertEqual(self.delays[-1], 2800)
        flow.hit()
        flow.stand()
        self.assertEqual(flow.game.table, result)
        self.tasks['turn']()
        self.assertEqual(flow.game.table.phase, Phase.PLAYER)
        self.assertIsNone(flow.game.table.result)
        self.assertIsNone(self.hands[-1][0].cards[1])
        self.assertEqual(flow.game.score.wins, 1)
        self.assertEqual(self.tasks, {})

    def test_close_during_result_pause_cancels_restart_without_losing_unit(self):
        flow = self.make_flow(arranged_game(card('A'), card('8'), card('K'), card('9')))
        flow.advance()
        flow.advance()
        restart = self.tasks['turn']
        self.assertEqual(flow.close().games, 1)
        restart()
        self.assertEqual(self.tasks, {})
        self.assertEqual(flow.game.score.games, 1)
        self.assertEqual(self.hands[-1][0].cards, ())

    def test_consecutive_naturals_each_reveal_before_their_result_pause(self):
        flow = self.make_flow(arranged_game(card('A'), card('8'), card('K'), card('9')))
        flow.advance()
        flow.advance()
        self.tasks['turn']()
        self.assertEqual(flow.game.score.games, 1)
        self.assertIsNone(flow.game.table.result)
        self.assertIsNone(self.hands[-1][0].cards[1])
        self.assertEqual(self.delays[-1], 500)
        flow.advance()
        self.assertTrue(self.hands[-1][1])
        flow.advance()
        self.assertEqual(flow.game.score.games, 2)
        self.assertEqual(self.delays[-1], 2800)

    def test_dealer_draws_are_separately_presented_and_input_stays_blocked(self):
        flow = self.make_flow(arranged_game(
            card('10'), card('2'), card('8'), card('3'),
            card('10', 'hearts'), card('K'),
        ))
        flow.stand()
        flow.hit()
        flow.advance()
        flow.advance()
        self.assertEqual(len(self.hands[-1][0].cards), 3)
        self.assertIsNone(self.views[-1][0].result)
        flow.advance()
        self.assertEqual(len(self.hands[-1][0].cards), 4)
        self.assertEqual(flow.game.score.wins, 1)
