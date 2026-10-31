"""Every reachable open board supports the tactical statement Aiko makes."""

import unittest

from aiko_pet.games.tic_tac_toe import LINES, Board
from aiko_pet.games.tic_tac_toe_analysis import evaluate, read_board, winning_moves


class TicTacToeAnalysisTests(unittest.TestCase):
    def test_both_starters_all_reachable_open_boards(self):
        seen = set()
        stack = [Board(("",) * 9, mark) for mark in ("X", "O")]
        while stack:
            board = stack.pop()
            key = (board.cells, board.turn)
            if key in seen:
                continue
            seen.add(key)
            reading = read_board(board)
            if reading.event == "game_ttt_balanced":
                self.assertEqual(evaluate(board.cells, board.turn), 0)
            elif reading.event == "game_ttt_finish":
                self.assertIn(reading.target, winning_moves(board.cells, "O"))
            elif reading.event in ("game_ttt_block", "game_ttt_player_threat"):
                self.assertIn(reading.target, winning_moves(board.cells, "X"))
            elif reading.event == "game_ttt_fork":
                self.assertGreater(len(winning_moves(board.cells, "O")), 1)
            for i, value in enumerate(board.cells):
                if value:
                    continue
                cells = board.cells[:i] + (board.turn,) + board.cells[i + 1:]
                if not all(cells) and not any(
                    all(cells[j] == board.turn for j in line) for line in LINES
                ):
                    stack.append(Board(cells, "O" if board.turn == "X" else "X"))
        self.assertGreater(len(seen), 8000)

    def test_public_immediate_threat_and_mistake_have_real_targets(self):
        board = Board(("X", "X", "", "O", "", "", "", "", ""), "O")
        self.assertEqual(read_board(board).event, "game_ttt_block")
        self.assertEqual(read_board(board).target, 2)
        before = Board(("X", "X", "", "O", "O", "", "", "", ""), "O")
        after = Board(("X", "X", "", "O", "O", "", "O", "", ""), "X")
        self.assertEqual(read_board(after, before).event, "game_ttt_mistake")
        self.assertEqual(read_board(after, before).target, 6)
