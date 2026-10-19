"""Board input, round controls and care completion through the actual host."""

import tempfile
import unittest
from pathlib import Path

from aiko_pet.games.contracts import GameId
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.tic_tac_toe_window import TicTacToeWindow


class TicTacToeGuiTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = DesktopPet(store=StateStore(Path(folder.name) / "save.json"))
        self.addCleanup(self.pet.quit)
        self.pet._hover.open_game(GameId.TIC_TAC_TOE)
        self.game = self.pet._hover.game_window
        assert isinstance(self.game, TicTacToeWindow)
        self.game._sequence.game._random_index = lambda _size: 0

    def test_buttons_result_next_round_and_once_only_reward(self):
        game = self.game
        before = self.pet.state.fun
        for cell in (0, 8, 6):
            game.buttons[cell].invoke()
            self.assertTrue(all(b.cget("state") == "disabled" for b in game.buttons))
            game._sequence.advance()
        game.buttons[7].invoke()
        self.assertEqual(game._panel.next_button.cget("state"), "normal")
        self.assertEqual(game.buttons[7].cget("bg"), game.skin.accent)
        self.assertEqual(self.pet.state.fun, before)
        game._panel.next_button.invoke()
        self.assertEqual(game._sequence.game.board.turn, "O")
        game.close()
        after = self.pet.state.fun
        self.assertGreater(after, before)
        game.close()
        self.assertEqual(self.pet.state.fun, after)
        self.assertIsNone(self.pet._hover.game_window)

    def test_pending_turn_does_not_reward_and_callbacks_are_cancelled(self):
        before = self.pet.state.fun
        self.game.buttons[0].invoke()
        self.game.close()
        self.game._sequence.advance()
        self.assertEqual(self.pet.state.fun, before)
        self.assertIsNone(self.game._sequence.pending_timer)
