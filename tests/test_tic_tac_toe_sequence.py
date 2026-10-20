"""Turn pacing and cancellation without sleeping or opening widgets."""

import unittest

from aiko_pet.games.tic_tac_toe import TicTacToe
from aiko_pet.ui.windows.tic_tac_toe_sequence import TicTacToeSequence


class TicTacToeSequenceTests(unittest.TestCase):
    def setUp(self):
        self.tasks = {}
        self.views = []
        self.lines = []
        self.rounds = []
        self.flow = TicTacToeSequence(
            schedule=self.schedule, cancel=lambda token: self.tasks.pop(token, None),
            present=lambda board, score: self.views.append((board, score)),
            say=lambda text, _ms: self.lines.append(text), animate=lambda _name: None,
            dialogue=lambda event: event,
            game=TicTacToe(random_index=lambda _size: 0),
            round_event=self.rounds.append,
        )

    def schedule(self, _ms, callback):
        self.tasks["turn"] = callback
        return "turn"

    def test_turn_blocks_second_choice_and_close_invalidates_callback(self):
        self.flow.greet()
        self.flow.choose(0)
        board = self.flow.game.board
        self.flow.choose(1)
        self.assertEqual(self.flow.game.board, board)
        stale = self.tasks["turn"]
        summary = self.flow.close()
        stale()
        self.assertEqual(summary.games, 0)
        self.assertEqual(self.tasks, {})
        self.assertEqual(self.flow.game.board, board)

    def test_finished_result_counts_once_and_next_round_starts_with_aiko(self):
        self.flow.greet()
        for cell in (0, 8, 6):
            self.flow.choose(cell)
            self.flow.advance()
        self.flow.choose(7)
        self.assertEqual(self.flow.game.score.wins, 1)
        self.assertEqual([e.outcome for e in self.rounds], [None, "win"])
        self.assertEqual(self.lines[-1], "game_round_player_win")
        self.flow.next_round()
        self.assertEqual(self.rounds[-1].number, 2)
        self.assertIsNone(self.rounds[-1].outcome)
        self.assertEqual(self.flow.game.board.turn, "O")
        self.flow.advance()
        self.assertEqual(self.flow.game.board.cells[4], "O")
        self.assertEqual(self.flow.close().games, 1)
        self.assertEqual(self.flow.close().games, 1)
