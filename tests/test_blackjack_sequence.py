"""Reveal/settlement ordering and cancellation using an injected clock."""

import unittest

from test_blackjack import arranged_game, card

from aiko_pet.games.contracts import BlackjackDecisionReason, BlackjackDetails
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

    def until(self, flow, predicate):
        for _ in range(80):
            if predicate():
                return
            flow.advance()
        self.fail("Logical sequence did not reach its boundary")

    def ready(self, flow):
        self.until(flow, lambda: not flow.busy)

    def settle(self, flow):
        self.until(flow, lambda: flow.game.score.games == 1)

    def test_initial_deal_is_alternating_masked_and_landing_based(self):
        flow = self.make_flow(arranged_game(
            card('10'), card('9'), card('8'), card('7')))
        self.assertEqual(self.views[-1][0].player, ())
        flow.hit()
        self.assertEqual(len(flow.game.table.player), 2)
        flow.advance()  # greeting
        flow.advance()  # shuffle
        flow.advance()  # player one lands
        self.assertEqual(len(self.views[-1][0].player), 1)
        self.assertEqual(self.views[-1][0].dealer, ())
        flow.advance()
        self.assertEqual(len(self.hands[-1][0].cards), 1)
        flow.advance()
        flow.advance()
        self.assertFalse(flow.busy)
        self.assertIsNone(self.hands[-1][0].cards[1])
        self.assertEqual(self.views[-1][0].player_total, 18)

    def test_natural_reveals_before_exactly_once_completion(self):
        flow = self.make_flow(arranged_game(card('A'), card('8'), card('K'), card('9')))
        self.settle(flow)
        self.assertTrue(any(flip for _, flip in self.hands))
        self.assertEqual([e.outcome for e in self.rounds], [None, 'win'])
        self.assertEqual(self.rounds[1].details, BlackjackDetails(
            21, 17, BlackjackDecisionReason.PLAYER_BLACKJACK))
        self.assertEqual(self.rounds[0].identity, self.rounds[1].identity)
        self.assertEqual(flow.close().wins, 1)
        self.assertEqual(flow.close().games, 1)
        self.assertEqual(self.hands[-1][0].cards, ())

    def test_bust_card_and_sum_wait_for_landing_and_bank_does_not_draw(self):
        flow = self.make_flow(arranged_game(
            card('10'), card('2'), card('8'), card('3'), card('9')))
        self.ready(flow)
        flow.hit()
        flow.hit()
        self.assertEqual(len(self.views[-1][0].player), 2)
        self.assertEqual(self.views[-1][0].player_total, 18)
        flow.advance()
        self.assertEqual(self.views[-1][0].player_total, 27)
        self.settle(flow)
        self.assertEqual(len(self.hands[-1][0].cards), 2)
        self.assertEqual(self.rounds[-1].details, BlackjackDetails(
            27, 5, BlackjackDecisionReason.PLAYER_BUST))

    def test_result_speech_aside_emote_restore_precede_restart_countdown(self):
        flow = self.make_flow(arranged_game(card('A'), card('8'), card('K'), card('9')))
        self.settle(flow)
        flow.hit()
        self.assertEqual(self.lines[-1], 'game_bj_win')
        flow.advance()
        self.assertEqual(self.lines[-1], 'game_bj_aside')
        flow.advance()
        self.assertEqual(self.delays[-1], 950)
        flow.advance()
        self.assertEqual(self.delays[-1], 2800)
        flow.advance()  # gather
        self.assertEqual(flow.game.score.games, 1)
        flow.advance()  # restart, remains locked through new deal
        self.assertTrue(flow.busy)
        self.assertEqual(len(self.rounds), 3)
        self.assertIsNone(self.rounds[-1].outcome)

    def test_close_cancels_every_logical_phase_and_stale_callback(self):
        for stop in range(14):
            with self.subTest(stop=stop):
                flow = self.make_flow(arranged_game(
                    card('A'), card('8'), card('K'), card('9')))
                for _ in range(stop):
                    flow.advance()
                stale = self.tasks.get('turn')
                score = flow.close()
                if stale:
                    stale()
                self.assertEqual(flow.close(), score)
                self.assertEqual(self.hands[-1][0].cards, ())
                self.assertIsNone(flow.pending_timer)

    def test_dealer_draws_land_one_at_a_time(self):
        flow = self.make_flow(arranged_game(
            card('10'), card('2'), card('8'), card('3'),
            card('10', 'hearts'), card('K')))
        self.ready(flow)
        flow.stand()
        flow.advance()  # stand acknowledgement
        flow.advance()  # reveal announcement
        flow.advance()  # bank mutates, third card not yet visible
        self.assertEqual(len(self.hands[-1][0].cards), 2)
        flow.advance()
        self.assertEqual(len(self.hands[-1][0].cards), 3)
        self.settle(flow)
        self.assertEqual(len(self.hands[-1][0].cards), 4)
        self.assertEqual(flow.game.score.wins, 1)
