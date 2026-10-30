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

    def wait_for(self, predicate, limit=90):
        for _ in range(limit * 10):
            if predicate():
                return
            self.timing.advance(.1)
        self.fail("Native choreography did not reach its boundary")

    def ready(self, game):
        self.wait_for(lambda: not game._sequence.busy)

    def test_real_deal_uses_one_deck_and_equal_card_sizes_without_early_totals(self):
        game = self.open_game(arranged_game(
            card('10'), card('9'), card('8'), card('7'), card('K')))
        self.assertEqual(game._visible.player, ())
        game.hit()
        self.assertEqual(len(game._sequence.game.table.player), 2)
        self.ready(game)
        hand = self.pet._game_visuals.hand
        self.assertIsNone(hand._hand.cards[1])
        assert hand.canvas is not None
        for item in hand.canvas.find_all():
            image = hand.canvas.itemcget(item, 'image')
            self.assertEqual(self.pet.root.tk.call('image', 'width', image), 128)
        assert game._motion is not None
        self.assertIn('deck', game._motion.effects._windows)
        self.assertEqual(game.hit_button.cget('image'), '')
        before = self.pet.state.fun
        game.stand()
        self.wait_for(lambda: game._sequence.game.score.games == 1)
        self.assertIsNone(game._panel.next_button)
        game.close()
        self.assertGreater(self.pet.state.fun, before)
        self.assertEqual(hand.windows, ())
        self.assertIsNone(self.pet._speech.bubble)

    def test_close_at_shuffle_flight_flip_and_result_cancels_all_owners(self):
        for seconds in (1, 5, 6, 10, 16):
            with self.subTest(seconds=seconds):
                game = self.open_game(arranged_game(
                    card('A'), card('8'), card('K'), card('9')))
                self.timing.advance(seconds)
                game.close()
                after_close = self.pet.state.fun
                self.timing.advance(30)
                self.assertLessEqual(self.pet.state.fun, after_close)
                self.assertEqual(self.pet._game_visuals.hand.windows, ())
                self.assertFalse(game.window.winfo_exists())
                self.assertIsNone(game._sequence.pending_timer)
                self.assertEqual(game._motion.effects._windows, {})
                self.assertFalse(self.pet._animated.game_mode)

    def test_long_player_hand_stays_inside_the_card_area(self):
        game = self.open_game(arranged_game(
            card('2'), card('9'), card('3'), card('7')))
        table = Table(STANDARD_DECK[:11], (None,), 20, Phase.PLAYER, None)
        game._present(table, game._sequence.game.score)
        game.window.update()
        for item in game.player_cards.find_all():
            if game.player_cards.type(item) != 'image':
                continue
            bounds = game.player_cards.bbox(item)
            assert bounds is not None
            self.assertGreaterEqual(bounds[0], 0)
            self.assertGreaterEqual(bounds[1], 0)
            self.assertLessEqual(bounds[2], game.player_cards.winfo_width())
            self.assertLessEqual(bounds[3], game.player_cards.winfo_height())

    def test_scale_move_keeps_panel_fixed_and_cards_at_128(self):
        game = self.open_game(arranged_game(
            card('10'), card('9'), card('8'), card('7')))
        self.ready(game)
        self.pet.root.update()
        panel_geometry = game.window.winfo_geometry()
        hand = self.pet._game_visuals.hand
        assert hand.window is not None
        geometry = hand.window.winfo_geometry()
        self.pet.toggle_scale()
        self.pet._place_x(1)
        self.pet.root.update()
        self.assertEqual(game.window.winfo_geometry(), panel_geometry)
        self.assertNotEqual(hand.window.winfo_geometry(), geometry)
        assert hand.canvas is not None
        image = hand.canvas.itemcget('card_0', 'image')
        self.assertEqual(self.pet.root.tk.call('image', 'width', image), 128)
        with patch.object(hand.window, 'wm_attributes',
                          wraps=hand.window.wm_attributes) as attrs:
            self.pet._preferences.set_topmost(False)
        attrs.assert_called_once_with('-topmost', False)

    def test_result_finish_then_auto_gather_keeps_one_completed_receipt(self):
        game = self.open_game(arranged_game(
            card('10'), card('9'), card('8'), card('7'), card('K')))
        self.ready(game)
        game.stand()
        self.wait_for(lambda: game._sequence.game.score.games == 1)
        self.wait_for(lambda: not game._sequence.busy)
        self.assertEqual(game._sequence.game.score.games, 1)
        self.assertIsNone(self.pet._game_visuals.hand._hand.cards[1])

    def test_moving_panel_during_flight_and_shutdown_clear_effects(self):
        game = self.open_game(arranged_game(
            card('2'), card('9'), card('3'), card('7'), card('4')))
        self.ready(game)
        game.hit()
        self.timing.advance(.3)
        game.window.geometry('+300+100')
        self.timing.advance(.4)
        self.assertEqual(len(game._visible.player), 3)
        self.assertEqual(game.hit_button.cget('state'), 'normal')
        self.pet.quit()
        self.assertEqual(self.pet._game_visuals.hand._hand, HandView())
        self.assertEqual(game._motion.effects._windows, {})

    def test_new_panel_uses_left_side_at_right_edge(self):
        self.pet._place_x(10000)
        self.pet.root.update_idletasks()
        game = self.open_game(arranged_game(
            card('10'), card('9'), card('8'), card('7')))
        game.window.update_idletasks()
        self.assertLess(game.window.winfo_x() + game.window.winfo_width(),
                        self.pet.root.winfo_x())
