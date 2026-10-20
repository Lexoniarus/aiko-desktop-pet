"""Actual host wiring keeps Aiko's cards outside the player's panel."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_blackjack import arranged_game, card

from aiko_pet.games.blackjack import Phase, Table
from aiko_pet.games.contracts import GameId
from aiko_pet.games.playing_cards import STANDARD_DECK
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.view_models.game_models import HandView
from aiko_pet.ui.windows.blackjack_sequence import BlackjackSequence
from aiko_pet.ui.windows.blackjack_window import BlackjackWindow
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


class BlackjackGuiTests(unittest.TestCase):
    def setUp(self):
        self.timing = self.enterContext(ControlledTkTime())
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / 'save.json'),
        )
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
        self.assertIsNone(game._panel.next_button)
        self.assertIsNotNone(game._sequence.pending_timer)
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

    def test_player_cards_are_larger_and_the_draw_pile_is_the_hit_control(self):
        game = self.open_game(arranged_game(
            card('2'), card('9'), card('3'), card('7'), card('4'),
        ))
        for item in game.player_cards.find_all():
            image = game.player_cards.itemcget(item, 'image')
            self.assertEqual(self.pet.root.tk.call('image', 'width', image), 128)
        hand = self.pet._game_visuals.hand
        assert hand.canvas is not None
        aiko_image = hand.canvas.itemcget('card_0', 'image')
        self.assertEqual(self.pet.root.tk.call('image', 'width', aiko_image), 64)
        pile = self.pet._game_visuals.images.draw_pile()
        self.assertEqual(game.hit_button.cget('image'), str(pile))
        game.hit_button.invoke()
        self.assertEqual(len(game._sequence.game.table.player), 3)
        game.stand_button.invoke()
        game.hit_button.invoke()
        self.assertEqual(len(game._sequence.game.table.player), 3)

    def test_long_player_hand_stays_inside_the_larger_card_area(self):
        game = self.open_game(arranged_game(
            card('2'), card('9'), card('3'), card('7'),
        ))
        table = Table(STANDARD_DECK[:11], (None,), 20, Phase.PLAYER, None)
        game._present(table, game._sequence.game.score)
        # Windows maps the native panel through normal events, not only idle work.
        game.window.update()
        self.assertTrue(game.player_cards.winfo_ismapped())
        for item in game.player_cards.find_all():
            bounds = game.player_cards.bbox(item)
            assert bounds is not None
            self.assertGreaterEqual(bounds[0], 0)
            self.assertGreaterEqual(bounds[1], 0)
            self.assertLessEqual(bounds[2], game.player_cards.winfo_width())
            self.assertLessEqual(bounds[3], game.player_cards.winfo_height())

    def test_scale_move_and_topmost_are_forwarded_to_the_same_hand(self):
        self.open_game(arranged_game(card('10'), card('9'), card('8'), card('7')))
        hand = self.pet._game_visuals.hand
        window = hand.window
        assert window is not None
        self.pet.toggle_scale()
        self.pet._place_x(1)
        self.assertIs(hand.window, window)
        with patch.object(window, 'wm_attributes', wraps=window.wm_attributes) as attrs:
            self.pet._preferences.set_topmost(False)
        attrs.assert_called_once_with('-topmost', False)
        self.assertTrue(hand._hand.cards)

    def test_result_timer_starts_the_next_hand_with_a_fresh_masked_dealer(self):
        game = self.open_game(arranged_game(
            card('10'), card('9'), card('8'), card('7'), card('K'),
        ))
        game.stand()
        game._sequence.advance()
        game._sequence.advance()
        self.assertEqual(game._sequence.game.score.games, 1)
        self.assertIsNone(game._panel.next_button)
        self.timing.advance((BlackjackSequence.RESULT_PAUSE_MS - 1) / 1000)
        self.assertIsNotNone(game._sequence.game.table.result)
        self.timing.advance(.001)
        self.assertIsNone(game._sequence.game.table.result)
        self.assertIsNone(self.pet._game_visuals.hand._hand.cards[1])
        self.assertEqual(game._sequence.game.score.games, 1)
        self.assertEqual(game.hit_button.cget('state'), 'normal')

    def test_system_close_cleans_flip_and_rewards_only_completed_hands_once(self):
        for completed in (False, True):
            with self.subTest(completed=completed):
                game = self.open_game(arranged_game(
                    card('A'), card('8'), card('K'), card('9'),
                ))
                before = self.pet.state.fun
                game._sequence.advance()
                hand = self.pet._game_visuals.hand
                flip_timer = hand.pending_timer
                assert flip_timer is not None
                if completed:
                    game._sequence.advance()
                self.pet.root.tk.eval(game.window.protocol('WM_DELETE_WINDOW'))
                after = self.pet.state.fun
                game._sequence.advance()
                hand.advance_flip()
                game.close()
                self.assertNotIn(flip_timer, self.pet.root.tk.call('after', 'info'))
                self.assertIsNone(game._sequence.pending_timer)
                self.assertIsNone(hand.pending_timer)
                self.assertEqual(hand.windows, ())
                self.assertFalse(self.pet._game_visuals.images._images)
                self.assertFalse(self.pet._game_visuals.images._piles)
                self.assertFalse(game.window.winfo_exists())
                self.assertIsNone(self.pet._hover.game_window)
                self.assertFalse(self.pet._animated.game_mode)
                self.assertIsNone(self.pet._speech.bubble)
                self.assertEqual(self.pet.state.fun, after)
                if completed:
                    self.assertGreater(after, before)
                else:
                    self.assertEqual(after, before)

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

    def test_new_panel_uses_left_side_when_aiko_is_at_right_edge(self):
        self.pet._place_x(10000)
        self.pet.root.update_idletasks()
        game = self.open_game(arranged_game(
            card('10'), card('9'), card('8'), card('7'),
        ))
        game.window.update_idletasks()
        self.assertLess(
            game.window.winfo_x() + game.window.winfo_width(),
            self.pet.root.winfo_x(),
        )
