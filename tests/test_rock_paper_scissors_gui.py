"""Native isolated-save checks for the accepted Fingerduell flow."""
import tempfile
import unittest
from pathlib import Path

from aiko_pet.games.contracts import GameId
from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


class RockPaperScissorsWindowTests(unittest.TestCase):
    def setUp(self):
        self.clock = self.enterContext(ControlledTkTime())
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.pet = create_test_desktop(store=StateStore(Path(folder) / 'save.json'))
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        self.game = self.pet._hover.game_window
        self.assertIsInstance(self.game, RockPaperScissorsWindow)
        self.game._sequence._game._random_index = lambda _: 2

    def test_immediate_player_hand_then_actual_third_forward_reveal(self):
        self.game.choose(Move.ROCK)
        self.assertEqual(self.game.player_hand.itemcget(
            self.game._hand_image_item, 'state'), 'normal')
        self.assertEqual(self.game.score.games, 0)
        self.clock.advance(2.249)
        self.assertEqual(self.game.score.games, 0)
        self.clock.advance(.002)
        self.assertEqual(self.game.score.wins, 1)
        self.assertEqual(self.pet._speech._game_hand, Move.SCISSORS)
        self.assertEqual(self.game.buttons[Move.ROCK].cget('state'), 'normal')
        self.clock.advance(1.4)
        self.assertEqual(self.pet._speech._game_hand, Move.SCISSORS)
        self.assertIsNotNone(self.pet._speech.bubble)

    def test_new_choice_interrupts_third_recovery_and_preserves_count(self):
        self.game.choose(Move.ROCK)
        self.clock.advance(2.251)
        self.game.choose(Move.PAPER)
        self.assertEqual(self.game.score.games, 1)
        self.assertIsNone(self.pet._speech._game_hand)
        self.clock.advance(2.251)
        self.assertEqual(self.game.score.games, 2)
        self.game.close()
        self.clock.advance(8)
        self.assertIsNone(self.pet._speech.bubble)
        self.assertIsNone(self.pet._animated._game_clip)
        self.assertFalse(self.pet._animated.game_mode)

    def test_closing_before_reveal_never_completes_a_round(self):
        before = self.pet.state.fun
        self.game.choose(Move.ROCK)
        self.clock.advance(.5)
        self.game.close()
        self.clock.advance(5)
        self.assertEqual(self.game.score.games, 0)
        self.assertLessEqual(self.pet.state.fun, before)
        self.assertIsNone(self.pet._hover.game_window)

    def test_completed_then_aborted_hand_is_credited_once_on_close(self):
        before = self.pet.state.fun
        self.game.choose(Move.ROCK)
        self.clock.advance(2.251)
        self.game.choose(Move.PAPER)
        self.assertEqual(self.game.score.games, 1)
        self.game.close()
        self.assertGreater(self.pet.state.fun, before)
        after = self.pet.state.fun
        self.game.close()
        self.assertEqual(self.pet.state.fun, after)
