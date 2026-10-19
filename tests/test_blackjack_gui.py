"""Actual host wiring keeps Aiko's cards outside the player's panel."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_blackjack import arranged_game, card

from aiko_pet.games.contracts import GameId
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.view_models.game_models import HandView
from aiko_pet.ui.windows.blackjack_window import BlackjackWindow


class BlackjackGuiTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = DesktopPet(store=StateStore(Path(folder.name) / 'save.json'))
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False

    def open_game(self, game):
        with patch(
            'aiko_pet.ui.windows.blackjack_sequence.Blackjack', return_value=game,
        ):
            self.pet._hover.open_game(GameId.BLACKJACK)
        window = self.pet._hover.game_window
        assert isinstance(window, BlackjackWindow)
        return window

    def test_player_cards_and_floating_hand_speech_and_completion_are_separate(self):
        game = self.open_game(arranged_game(
            card('10'), card('9'), card('8'), card('7'), card('K'),
        ))
        hand = self.pet._game_visuals.hand
        self.assertIsNone(hand._hand.cards[1])
        self.assertEqual(len(game.player_cards.find_all()), 2)
        self.assertIn(hand.window, self.pet._overlay_windows())
        self.pet._speech.show_text('Eine kurze Bemerkung.', 2000)
        self.assertEqual(len(hand.windows), 1)
        game.stand_button.invoke()
        self.assertEqual(game.hit_button.cget('state'), 'disabled')
        game._sequence.advance()
        for _ in range(8):
            hand.advance_flip()
        before = self.pet.state.fun
        game._sequence.advance()
        self.assertEqual(game._panel.next_button.cget('state'), 'normal')
        game.close()
        self.assertGreater(self.pet.state.fun, before)
        self.assertIsNone(hand.window)
        self.assertIsNone(hand.pending_timer)
        self.assertIsNone(self.pet._speech.bubble)

    def test_close_during_flip_clears_cards_timers_and_never_rewards(self):
        game = self.open_game(arranged_game(card('A'), card('8'), card('K'), card('9')))
        before = self.pet.state.fun
        game._sequence.advance()
        self.assertIsNotNone(self.pet._game_visuals.hand.pending_timer)
        self.pet._hover.close_game()
        game._sequence.advance()
        self.pet._game_visuals.hand.advance_flip()
        self.assertEqual(self.pet.state.fun, before)
        self.assertEqual(self.pet._game_visuals.hand.windows, ())

    def test_scale_move_and_topmost_are_forwarded_to_the_same_hand(self):
        self.open_game(arranged_game(card('10'), card('9'), card('8'), card('7')))
        hand = self.pet._game_visuals.hand
        window = hand.window
        self.pet.toggle_scale()
        self.pet._place_x(1)
        self.assertIs(hand.window, window)
        with patch.object(window, 'wm_attributes', wraps=window.wm_attributes) as attrs:
            self.pet._preferences.set_topmost(False)
        attrs.assert_called_once_with('-topmost', False)
        self.assertTrue(hand._hand.cards)

    def test_failed_hand_presentation_closes_player_window_and_mode(self):
        hand = self.pet._game_visuals.hand
        with patch.object(hand, '_configure', side_effect=RuntimeError('native error')):
            with self.assertRaises(RuntimeError):
                self.open_game(arranged_game(
                    card('10'), card('9'), card('8'), card('7'),
                ))
        self.assertIsNone(self.pet._hover.game_window)
        self.assertFalse(self.pet._animated.game_mode)
        self.assertEqual(hand.windows, ())

    def test_shutdown_clears_overlay_before_final_save(self):
        self.open_game(arranged_game(card('10'), card('9'), card('8'), card('7')))
        self.pet.quit()
        self.assertEqual(self.pet._game_visuals.hand.windows, ())
        self.assertEqual(self.pet._game_visuals.hand._hand, HandView())
