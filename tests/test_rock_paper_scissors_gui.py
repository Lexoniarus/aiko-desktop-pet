"""Native isolated-save checks for the accepted Fingerduell flow."""
import tempfile
import time
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
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        self.game = game
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
        bubble = self.pet._speech.bubble
        assert bubble is not None

        def visible_text(widget):
            text = [str(widget.cget('text'))] if 'text' in widget.keys() else []
            return text + [value for child in widget.winfo_children()
                           for value in visible_text(child)]
        self.assertIn('Papier!', visible_text(bubble))
        self.clock.advance(.448)
        self.assertIn('Papier!', visible_text(bubble))
        self.clock.advance(.002)
        self.assertIsNot(self.pet._speech.bubble, bubble)
        self.clock.advance(.95)
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

    def test_all_hand_choices_keep_the_mat_and_player_window_fixed(self):
        self.pet.root.update()
        geometry = self.game.window.winfo_geometry()
        for move in Move:
            self.game.choose(move)
            self.clock.advance(2.251)
            self.pet.root.update()
            self.assertEqual(self.game.window.winfo_geometry(), geometry)
            bounds = self.game.player_hand.bbox(self.game._hand_image_item)
            assert bounds is not None
            left, top, right, bottom = bounds
            self.assertGreaterEqual(left, 0)
            self.assertGreaterEqual(top, 0)
            self.assertLessEqual(right, self.game.player_hand.winfo_width())
            self.assertLessEqual(bottom, self.game.player_hand.winfo_height())

    def test_game_gaze_never_enables_cursor_chasing_or_walk(self):
        visual = self.pet._animated
        self.assertIsNone(self.pet._visual.gaze_direction(
            (99999, 99999), game_mode=visual.game_mode,
        ))
        self.assertIsNone(self.pet._walk.step(
            time.monotonic(), .5, game_mode=visual.game_mode, attention_active=False,
        ))
        before = (self.pet.settings.x, self.pet.settings.y)
        self.game.choose(Move.ROCK)
        self.clock.advance(3)
        self.assertEqual((self.pet.settings.x, self.pet.settings.y), before)
        self.game.close()
        self.assertFalse(visual.game_mode)
