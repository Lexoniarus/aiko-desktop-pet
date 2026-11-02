"""Tk regression tests for Aiko's original speech and game-hand overlays."""

from __future__ import annotations

import sys
import tkinter as tk
import unittest
from unittest.mock import patch

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.ui.pet_view.speech_presenter import SpeechAnchor, SpeechPresenter
from tools.tk_test_time import ControlledTkTime


class SpeechPresenterTests(unittest.TestCase):
    def test_game_hand_survives_comment_and_emoji_expiry_but_not_game_close(self):
        self.presenter.begin_game()
        self.presenter.show_game_hand(Move.ROCK, 0)
        self.presenter.show_text("Schere, Stein, Papier!", 1800)
        self.assertEqual(self.presenter._game_hand, Move.ROCK)
        self.presenter.show_emote("star", 900)
        self.assertEqual(self.presenter._game_hand, Move.ROCK)
        hand = self.presenter.hand_bubble
        self.presenter._expire()
        self.assertIsNone(self.presenter.bubble)
        self.assertIs(self.presenter.hand_bubble, hand)
        self.assertIsNotNone(hand)
        self.assertEqual(self.presenter._game_hand, Move.ROCK)
        self.presenter.hide()
        self.assertIsNone(self.presenter.bubble)
        self.assertIsNone(self.presenter._game_hand)
        self.assertIsNone(self.presenter.hand_bubble)

    @classmethod
    def setUpClass(cls) -> None:
        try:
            window = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Tk display unavailable") from error
        window.destroy()

    def setUp(self) -> None:
        self.clock = self.enterContext(ControlledTkTime())
        self.root = tk.Tk()
        self.root.withdraw()
        self.anchor = SpeechAnchor(200, 500, 128)
        self.restacks: list[bool] = []
        self.presenter = SpeechPresenter(
            root=self.root, anchor=lambda: self.anchor,
            font_name="Segoe UI", always_on_top=lambda: False,
            restore_stack=lambda: self.restacks.append(True),
        )
        self.addCleanup(self.root.destroy)
        self.addCleanup(self.presenter.hide)

    def test_game_comments_use_the_prepared_asset_and_keep_the_speech_tail(self):
        self.presenter.begin_game()
        self.presenter.show_text("Dein Zug!", 900)
        self.root.update()
        images = self.presenter._ui_images
        assert images is not None
        self.assertIn("game_bubble_panel.png", images._images)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertIsInstance(bubble.winfo_children()[-1], tk.Canvas)

    def test_game_emote_has_no_outer_frame_or_second_tail_and_keeps_hand(self):
        self.presenter.begin_game()
        for hand in (False, True):
            if hand:
                self.presenter.show_game_hand(Move.ROCK, 0)
            self.presenter.show_text("Dein Zug!", 0)
            self.root.update()
            text_window = self.presenter.bubble
            assert text_window is not None
            geometry = (text_window.winfo_width(), text_window.winfo_height())
            self.presenter.show_emote("star", 900)
            self.root.update()
            window = self.presenter.bubble
            assert window is not None
            self.assertEqual((window.winfo_width(), window.winfo_height()), geometry)
            frame = window.winfo_children()[0]
            region = frame.winfo_children()[0]
            self.assertEqual(region.cget("background"),
                             "#ff00ff" if sys.platform == "win32" else "#202733")
            self.assertEqual(len(region.winfo_children()), 1)
            icon = region.winfo_children()[0]
            self.assertEqual(icon.cget("image"),
                             str(self.presenter.emote_images['star']))
            self.assertEqual(window.winfo_children(), [frame])
            self.assertFalse(any(isinstance(child, tk.Canvas)
                                 for child in frame.winfo_children()))
            if hand:
                self.assertEqual(self.presenter._game_hand, Move.ROCK)
                self.assertIn(Move.ROCK, self.presenter.game_hand_images)

    def test_side_hand_never_replaces_or_restarts_text_and_survives_text_expiry(self):
        self.presenter.begin_game()
        self.presenter.show_text('Ein vollständiger Ergebnissatz.', 6000)
        spoken, deadline = self.presenter.bubble, self.presenter.pending_timer
        self.clock.advance(2)
        self.presenter.show_game_hand(Move.PAPER, 0)
        self.root.update()
        hand = self.presenter.hand_bubble
        assert hand is not None and spoken is not None
        self.assertIs(self.presenter.bubble, spoken)
        self.assertEqual(self.presenter.pending_timer, deadline)
        self.assertIsNot(hand, spoken)
        self.assertGreaterEqual(hand.winfo_rootx(),
                                spoken.winfo_rootx() + spoken.winfo_width() + 8)
        position = hand.winfo_geometry()
        self.clock.advance(4.001)
        self.assertIsNone(self.presenter.bubble)
        self.assertIs(self.presenter.hand_bubble, hand)
        self.presenter.move()
        self.root.update()
        self.assertEqual(hand.winfo_geometry(), position)
        self.presenter.show_emote('star', 450)
        self.clock.advance(.451)
        self.assertIsNone(self.presenter.bubble)
        self.assertIs(self.presenter.hand_bubble, hand)
        self.assertEqual(self.presenter.windows, (hand,))

    def test_topmost_and_anchor_movement_include_both_owned_windows(self):
        self.presenter.begin_game()
        self.presenter.show_game_hand(Move.ROCK, 0)
        self.presenter.show_text('Das ist meine Hand.', 6000)
        spoken, hand = self.presenter.bubble, self.presenter.hand_bubble
        assert spoken is not None and hand is not None
        self.root.update()
        before = (spoken.winfo_geometry(), hand.winfo_geometry())
        self.anchor = SpeechAnchor(500, 600, 128)
        self.presenter.move()
        self.root.update()
        self.assertNotEqual(before, (spoken.winfo_geometry(), hand.winfo_geometry()))
        with (patch.object(spoken, 'wm_attributes') as text_attrs,
              patch.object(hand, 'wm_attributes') as hand_attrs):
            self.presenter.set_topmost(False)
        text_attrs.assert_called_once_with('-topmost', False)
        hand_attrs.assert_called_once_with('-topmost', False)

    def test_timed_hand_expiry_cannot_hide_ongoing_text(self):
        self.presenter.begin_game()
        self.presenter.show_text('Dieser Text bleibt länger lesbar.', 6000)
        spoken, deadline = self.presenter.bubble, self.presenter.pending_timer
        self.presenter.show_game_hand(Move.ROCK, 900)
        self.clock.advance(.901)
        self.assertIsNone(self.presenter.hand_bubble)
        self.assertIs(self.presenter.bubble, spoken)
        self.assertEqual(self.presenter.pending_timer, deadline)
        self.assertIsNone(self.presenter._game_hand)

    def test_side_pair_clamps_at_edges_and_wraps_inside_a_narrow_screen(self):
        self.presenter.begin_game()
        with (patch.object(self.root, 'winfo_screenwidth', return_value=320),
              patch.object(self.root, 'winfo_screenheight', return_value=480)):
            self.presenter.show_text('Ein längerer Satz zum gut lesbaren Umbruch. ' * 3,
                                     9000)
            self.presenter.show_game_hand(Move.SCISSORS, 0)
            for anchor in (SpeechAnchor(0, 0, 128), SpeechAnchor(190, 450, 128)):
                self.anchor = anchor
                self.presenter.move()
                self.root.update()
                spoken, hand = self.presenter.bubble, self.presenter.hand_bubble
                assert spoken is not None and hand is not None
                for window in (spoken, hand):
                    self.assertGreaterEqual(window.winfo_x(), 0)
                    self.assertGreaterEqual(window.winfo_y(), 0)
                    self.assertLessEqual(window.winfo_x() + window.winfo_width(), 320)
                    self.assertLessEqual(window.winfo_y() + window.winfo_height(), 480)
                self.assertLessEqual(spoken.winfo_x() + spoken.winfo_width() + 8,
                                     hand.winfo_x())
                label = self.presenter._game_comment_label
                assert label is not None and label.master is not None
                self.assertGreaterEqual(label.master.winfo_height(),
                                        label.winfo_reqheight())

    def test_queued_old_expiry_cannot_remove_a_new_game_comment(self):
        self.presenter.begin_game()
        self.presenter.show_text("Die erste Ansage.", 1800)
        old = self.presenter.bubble
        assert old is not None
        self.presenter.show_emote("star", 900)
        current = self.presenter.bubble
        timer = self.presenter.pending_timer
        self.presenter._expire_current(old)
        self.assertIs(self.presenter.bubble, current)
        self.assertEqual(self.presenter.pending_timer, timer)

    def test_cursor_cue_is_nonblocking_and_cannot_replace_existing_speech(self):
        self.presenter.show_cursor_emote("question", 1500)
        self.assertIsNotNone(self.presenter.bubble)
        self.assertFalse(self.presenter.blocks_contact)
        self.presenter.hide()
        self.presenter.show_text("Geschichte", 6000)
        before = self.presenter.bubble
        self.presenter.show_cursor_emote("drops", 1500)
        self.assertIs(self.presenter.bubble, before)
        self.assertTrue(self.presenter.blocks_contact)
        self.presenter.hide()
        self.assertFalse(self.presenter.blocks_contact)

    def test_warning_reports_actual_vacant_slot_without_contact_lock(self):
        self.assertTrue(self.presenter.show_cursor_warning("Langsamer!", 2000))
        before = self.presenter.bubble
        self.assertFalse(self.presenter.blocks_contact)
        self.assertFalse(self.presenter.show_cursor_warning("Noch einmal", 2000))
        self.assertIs(before, self.presenter.bubble)
        self.presenter.hide()
        self.presenter.show_text("Geschichte", 6000)
        self.assertFalse(self.presenter.show_cursor_warning("Langsamer!", 2000))
        self.assertTrue(self.presenter.blocks_contact)

    def test_speech_renders_plain_text_with_existing_tail(self) -> None:
        self.presenter.show_text("Hallo <b>Browser</b>!", 6000)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertEqual(len(bubble.winfo_children()), 2)
        frame = bubble.winfo_children()[0]
        self.assertEqual(
            frame.winfo_children()[0].cget("text"), "Hallo <b>Browser</b>!",
        )
        self.assertTrue(self.restacks)
        self.assertIsNotNone(self.presenter.pending_timer)
        self.presenter.hide()
        self.assertIsNone(self.presenter.bubble)
        self.assertIsNone(self.presenter.pending_timer)

    def test_new_speech_replaces_old_bubble_and_moves_with_anchor(self) -> None:
        self.presenter.show_text("Vorher", 6000)
        previous = self.presenter.bubble
        self.anchor = SpeechAnchor(360, 500, 128)
        self.presenter.show_text("Nachher", 6000)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertIsNot(bubble, previous)
        self.assertEqual(
            bubble.winfo_children()[0].winfo_children()[0].cget("text"),
            "Nachher",
        )
        self.assertFalse(bool(previous and previous.winfo_exists()))

    def test_aikos_game_bubble_shows_only_her_hand(self) -> None:
        self.presenter.show_game_hand(Move.ROCK, 2600)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertEqual(len(bubble.winfo_children()), 2)
        self.assertEqual(set(self.presenter.game_hand_images), {Move.ROCK})
        self.assertEqual(self.presenter.game_hand_images[Move.ROCK].width(), 64)
        frame = bubble.winfo_children()[0]
        panel = next(
            child for child in frame.winfo_children() if isinstance(child, tk.Frame)
        )
        labels = [
            str(child.cget("text")) for child in panel.winfo_children()
            if isinstance(child, tk.Label)
        ]
        self.assertIn("Ich nehme ...", labels)
        self.assertNotIn("Du", labels)
        self.assertIsNotNone(self.presenter.pending_timer)
        self.root.update_idletasks()
        position = bubble.winfo_geometry()
        self.anchor = SpeechAnchor(460, 500, 128)
        self.presenter.move()
        self.root.update_idletasks()
        self.assertNotEqual(bubble.winfo_geometry(), position)
        self.presenter.show_text("Wieder normal", 2000)
        self.assertIsNotNone(self.presenter.bubble)

    def test_missing_emote_does_not_hide_previous_speech(self) -> None:
        self.presenter.show_text("Bleibt", 2000)
        old = self.presenter.bubble
        with self.assertRaises(ValueError):
            self.presenter.show_emote("invalid-emote")
        self.assertIs(self.presenter.bubble, old)


if __name__ == "__main__":
    unittest.main()
