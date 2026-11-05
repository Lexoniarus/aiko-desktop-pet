"""Public tactical comments have explicit board examples and target cells."""

import unittest

from aiko_pet.games.tic_tac_toe import Board
from aiko_pet.games.tic_tac_toe_analysis import evaluate, read_board, winning_moves


def board(cells: str, turn: str) -> Board:
    return Board(tuple("" if cell == "." else cell for cell in cells), turn)


class TicTacToeAnalysisTests(unittest.TestCase):
    def test_public_tactics_match_known_boards(self):
        cases = (
            (".........", "X", "balanced", 4),
            (".........", "O", "balanced", 4),
            ("OO.XX....", "O", "finish", 2),
            ("XX.O.....", "O", "block", 2),
            ("XX.O...O.", "X", "player_threat", 2),
            ("OXOXO....", "X", "fork", 6),
            ("OO......X", "X", "threat", 2),
            ("OX..O...X", "O", "forced_aiko", 4),
            ("XO..X...O", "X", "forced_player", 4),
        )
        for cells, turn, event, target in cases:
            with self.subTest(cells=cells, turn=turn):
                reading = read_board(board(cells, turn))
                self.assertEqual(reading.event, "game_ttt_" + event)
                self.assertEqual(reading.target, target)

    def test_mistakes_distinguish_losing_from_giving_up_a_win(self):
        for before, after, event, target in (
            ("XX.OO....", "XX.OO.O..", "mistake", 6),
            ("OX..O...X", "OXO.O...X", "mistake_draw", 2),
        ):
            with self.subTest(event=event):
                reading = read_board(board(after, "X"), board(before, "O"))
                self.assertEqual(reading.event, "game_ttt_" + event)
                self.assertEqual(reading.target, target)

    def test_evaluation_and_winning_cells_have_independent_expected_results(self):
        self.assertEqual(winning_moves(board("OXOXO....", "X").cells, "O"), (6, 8))
        self.assertEqual(winning_moves(board("XXXOO....", "O").cells, "X"), ())
        for cells, turn, expected in (
            ("OOOXX....", "X", 1),
            ("XXXOO....", "O", -1),
            ("XOXXOOOXX", "O", 0),
        ):
            with self.subTest(cells=cells):
                self.assertEqual(evaluate(board(cells, turn).cells, turn), expected)
