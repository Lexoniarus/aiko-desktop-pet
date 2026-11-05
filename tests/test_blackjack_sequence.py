"""Reveal/settlement ordering and cancellation using an injected clock."""

import unittest

from support.games import arranged_game, card

from aiko_pet.games.contracts import BlackjackDecisionReason, BlackjackDetails
from aiko_pet.presentation.games.blackjack_sequence import BlackjackSequence
from tools.reaction_test_support import FakeScheduler


class BlackjackSequenceTests(unittest.TestCase):
    def make_flow(self, game):
        self.clock = FakeScheduler()
        self.tasks = self.clock.callbacks
        self.hands = []
        self.views = []
        self.lines = []
        self.delays = []
        self.rounds = []

        def schedule(delay, callback):
            self.delays.append(delay)
            return self.clock.schedule(delay, callback)

        flow = BlackjackSequence(
            schedule=schedule, cancel=self.clock.cancel,
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

    def test_result_and_new_deal_continue_without_advancing_any_speech_timer(self):
        flow = self.make_flow(arranged_game(
            card('10'), card('9'), card('8'), card('7'), card('K')))
        self.ready(flow)
        flow.stand()
        self.settle(flow)
        self.assertEqual(self.lines, ['game_bj_welcome', 'game_bj_stand'])
        self.assertTrue(flow._comments.active)
        self.assertEqual(self.delays[-1], 4500)
        flow.advance()  # result view ends; gather starts even with speech still active
        self.assertEqual(self.delays[-1], 450)
        self.assertEqual(flow.game.score.games, 1)
        flow.advance()  # restart goes directly to shuffle
        self.assertEqual(len(self.rounds), 3)
        self.assertIsNone(self.rounds[-1].outcome)
        self.assertEqual(self.delays[-1], 900)
        self.ready(flow)
        self.assertFalse(flow.busy)
        self.assertTrue(flow._comments.active)
        self.assertEqual(self.lines.count('game_bj_welcome'), 1)
        flow.greet()
        self.assertEqual(self.lines.count('game_bj_welcome'), 1)
        flow.close()
        self.assertFalse(self.tasks)

    def test_close_cancels_every_logical_phase_and_stale_callback(self):
        for stop in range(14):
            with self.subTest(stop=stop):
                flow = self.make_flow(arranged_game(
                    card('A'), card('8'), card('K'), card('9')))
                for _ in range(stop):
                    flow.advance()
                token = flow.pending_timer
                stale = self.tasks[token][1] if token is not None else None
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
        flow.advance()  # flip finishes; bank mutates, third card not yet visible
        self.assertEqual(len(self.hands[-1][0].cards), 2)
        flow.advance()
        self.assertEqual(len(self.hands[-1][0].cards), 3)
        self.settle(flow)
        self.assertEqual(len(self.hands[-1][0].cards), 4)
        self.assertEqual(flow.game.score.wins, 1)
