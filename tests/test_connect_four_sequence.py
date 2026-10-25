"""Controlled asynchronous search, animation, reading time and stale callbacks."""

import unittest
from concurrent.futures import Executor, Future
from typing import cast
from unittest.mock import Mock

from aiko_pet.games.connect_four import ConnectFourSession
from aiko_pet.ui.windows.connect_four_sequence import ConnectFourSequence


class ConnectFourSequenceTests(unittest.TestCase):
    def setUp(self):
        self.tasks = {}
        self.serial = 0
        self.views, self.lines, self.events, self.emotes = [], [], [], []
        self.futures = []
        self.executor = Mock(spec=Executor)
        self.executor.submit.side_effect = self.submit
        self.flow = self.make_flow()
        self.addCleanup(self.flow.close)

    def submit(self, *_args):
        future = Future()
        self.futures.append(future)
        return future

    def schedule(self, milliseconds, callback):
        self.serial += 1
        token = str(self.serial)
        self.tasks[token] = milliseconds, callback
        return token

    def make_flow(self, game=None):
        return ConnectFourSequence(
            schedule=self.schedule, cancel=lambda token: self.tasks.pop(token, None),
            present=lambda *view: self.views.append(view),
            say=lambda text, ms: self.lines.append((text, ms)),
            animate=lambda _clip: None, emote=lambda *item: self.emotes.append(item),
            dialogue=lambda event: event, round_event=self.events.append,
            executor=cast(Executor, self.executor), game=game,
        )

    def advance_callback(self):
        token = next(iter(self.tasks))
        _, callback = self.tasks.pop(token)
        callback()

    def finish_drop(self):
        for _ in range(6):
            self.advance_callback()

    def test_first_choice_during_greeting_counts_and_drop_blocks_double_input(self):
        self.flow.greet()
        self.assertGreaterEqual(self.lines[0][1], 4000)
        self.assertFalse(self.flow.busy)
        self.assertIsNone(self.flow.pending_timer)
        self.assertFalse(any(self.flow.game.board.cells))
        self.flow.choose(3)
        board = self.flow.game.board
        self.flow.choose(4)
        self.assertIs(self.flow.game.board, board)
        self.assertIsNotNone(self.views[-1][-1])
        self.finish_drop()
        self.assertEqual(len(self.futures), 1)
        self.assertEqual(self.flow.game.board.cells[38], 1)
        self.futures[0].set_result(0)
        self.advance_callback()
        self.finish_drop()
        self.assertFalse(self.flow.busy)
        self.assertEqual(self.flow.game.board.cells[35], 2)

    def test_close_invalidates_a_running_search_and_every_stale_callback(self):
        self.flow.greet()
        self.flow.choose(3)
        self.finish_drop()
        future = self.futures[0]
        future.set_running_or_notify_cancel()
        stale = next(iter(self.tasks.values()))[1]
        before = self.flow.game.board
        summary = self.flow.close()
        future.set_result(0)
        stale()
        self.assertIs(self.flow.game.board, before)
        self.assertEqual(summary.games, 0)
        self.assertEqual(self.tasks, {})
        self.executor.shutdown.assert_called_once_with(wait=False, cancel_futures=True)

    def test_unready_search_polls_without_advancing_live_game(self):
        self.flow.greet()
        self.flow.choose(0)
        self.finish_drop()
        board = self.flow.game.board
        self.advance_callback()
        self.assertIs(self.flow.game.board, board)
        self.assertEqual(next(iter(self.tasks.values()))[0], 20)

    def test_completed_round_counts_once_and_next_starter_is_aiko(self):
        game = ConnectFourSession()
        for column in (0, 0, 1, 1, 2, 2):
            game.play(column, game.board.turn)
        self.flow.close()
        self.flow = self.make_flow(game)
        self.addCleanup(self.flow.close)
        self.flow.greet()
        self.flow.choose(3)
        self.finish_drop()
        self.assertEqual(game.score.wins, 1)
        self.assertEqual([event.outcome for event in self.events], [None, "win"])
        self.assertEqual(self.emotes[-1], ("faceSad", 800))
        self.flow.next_round()
        self.assertEqual(game.board.winner, 1)
        self.advance_callback()  # Emote before the outcome text.
        self.advance_callback()  # Complete the full outcome reading time.
        self.assertFalse(self.flow.busy)
        self.flow.next_round()
        self.assertEqual(game.board.turn, 2)
        self.assertEqual(len(self.futures), 1)
        self.assertEqual(self.flow.close().wins, 1)
        self.assertEqual(self.flow.close().wins, 1)

    def test_stale_drop_callback_cannot_override_a_new_timer(self):
        self.flow.greet()
        self.flow.choose(0)
        stale = next(iter(self.tasks.values()))[1]
        self.advance_callback()
        expected = self.flow.pending_timer
        frame = self.views[-1][-1]
        stale()
        self.assertEqual(self.flow.pending_timer, expected)
        self.assertIs(self.views[-1][-1], frame)

    def test_a_real_block_comment_uses_one_emote_and_full_reading_time(self):
        game = ConnectFourSession()
        for column in (0, 6, 1, 6, 2):
            game.play(column, game.board.turn)
        self.flow.close()
        self.flow = self.make_flow(game)
        self.addCleanup(self.flow.close)
        self.flow.greet()
        self.advance_callback()
        self.futures[0].set_result(3)
        self.advance_callback()
        self.finish_drop()
        self.assertEqual(self.emotes[-1], ("idea", 800))
        self.advance_callback()
        self.assertEqual(self.lines[-1][0], "game_c4_block")
        self.assertTrue(self.flow.busy)
        self.advance_callback()
        self.assertFalse(self.flow.busy)
