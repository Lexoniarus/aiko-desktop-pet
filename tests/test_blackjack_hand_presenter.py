"""Card hover/flip lifetime on Tk, isolated from speech and pet input."""

import tkinter as tk
import unittest
from dataclasses import replace
from unittest.mock import patch

from aiko_pet.games.playing_cards import Card
from aiko_pet.ui.common.playing_card_images import PlayingCardImages
from aiko_pet.ui.pet_view.blackjack_hand_presenter import BlackjackHandPresenter
from aiko_pet.ui.view_models.game_models import HandAnchor, HandView


class BlackjackHandPresenterTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.anchor = HandAnchor(100, 400, 192, 208, 0, 0, 1280, 984, 1)
        self.images = PlayingCardImages(self.root)
        self.addCleanup(self.images.clear)
        self.configured = []
        self.hand = BlackjackHandPresenter(
            self.root, images=self.images, anchor=lambda: self.anchor,
            topmost=lambda: False, configure_window=self.configured.append,
            restore_stack=lambda: True,
        )
        self.addCleanup(self.hand.hide)
        self.visible = Card("hearts", "A")
        self.secret = Card("spades", "Q")

    def test_hover_does_not_reveal_or_forward_to_pet_input(self):
        self.hand.show(HandView((self.visible, None)))
        assert self.hand.window is not None
        assert self.hand.canvas is not None
        self.hand.window.update()
        event = tk.Event()
        event.x, event.y = 70, 25
        self.hand._motion(event)
        self.assertEqual(self.hand._hover, 1)
        image = self.hand.canvas.itemcget("card_1", "image")
        self.assertEqual(image, str(self.images.get(None, 2)))
        self.hand.canvas.event_generate("<ButtonPress-1>", x=70, y=25)
        self.assertEqual(self.hand.canvas.itemcget("card_1", "image"), image)
        self.assertEqual(len(self.configured), 1)

    def test_flip_switches_face_at_midpoint_and_hide_cancels_frames(self):
        self.hand.show(HandView((self.visible, None)))
        self.hand.show(HandView((self.visible, self.secret)), flip=True)
        assert self.hand.canvas is not None
        self.assertEqual(
            self.hand.canvas.itemcget("card_1", "image"), str(self.images.get(None, 2)),
        )
        for _ in range(4):
            self.hand.advance_flip()
        self.assertEqual(
            self.hand.canvas.itemcget("card_1", "image"),
            str(self.images.get(self.secret, 2, compression=8)),
        )
        self.assertIsNotNone(self.hand.pending_timer)
        self.hand.hide()
        self.hand.advance_flip()
        self.assertEqual(self.hand.windows, ())
        self.assertIsNone(self.hand.pending_timer)

    def test_queued_old_flip_cannot_advance_a_new_hand(self):
        self.hand.show(HandView((self.visible, None)))
        self.hand.show(HandView((self.visible, self.secret)), flip=True)
        generation = self.hand._generation
        self.hand.show(HandView((self.visible, None)))
        self.hand._flip_if_current(generation)
        self.assertEqual(self.hand._frame, 0)
        self.assertEqual(self.hand._hand.cards[1], None)
        self.assertIsNone(self.hand.pending_timer)

    def test_move_scale_and_topmost_update_the_same_overlay(self):
        self.hand.show(HandView((self.visible, None)))
        window = self.hand.window
        assert window is not None
        self.anchor = replace(self.anchor, x=1250, scale=2)
        self.hand.move()
        window.update_idletasks()
        self.assertIs(self.hand.window, window)
        self.assertLessEqual(window.winfo_x() + window.winfo_width(), 1280)
        self.assertLessEqual(window.winfo_y() + window.winfo_height(), 984)
        with patch.object(window, "wm_attributes", wraps=window.wm_attributes) as attrs:
            self.hand.set_topmost(True)
        attrs.assert_called_once_with("-topmost", True)

    def test_caption_fits_without_canvas_text_fragments_at_large_fonts(self):
        original = self.root.tk.call("tk", "scaling")
        self.addCleanup(self.root.tk.call, "tk", "scaling", original)
        for scaling in (1.0, 1.67, 2.67):
            with self.subTest(scaling=scaling):
                self.hand.hide()
                self.root.tk.call("tk", "scaling", scaling)
                self.hand._caption_measure.configure(font=("Segoe UI", 9, "bold"))
                self.anchor = replace(self.anchor, y=980)
                for cards in ((self.visible,), (self.visible, None),
                              (self.visible, self.secret)):
                    self.hand.show(HandView(cards))
                    self.root.update()
                    caption = self.hand.caption
                    canvas = self.hand.canvas
                    window = self.hand.window
                    assert caption is not None and canvas is not None
                    assert window is not None
                    self.assertTrue(caption.winfo_ismapped())
                    self.assertGreaterEqual(caption.winfo_height(),
                                            caption.winfo_reqheight())
                    self.assertLessEqual(caption.winfo_y() + caption.winfo_height(),
                                         window.winfo_height())
                    self.assertLessEqual(window.winfo_y() + window.winfo_height(),
                                         self.anchor.bottom)
                    self.assertTrue(all(canvas.type(item) == 'image'
                                        for item in canvas.find_all()))
                    if cards[-1] is None:
                        self.assertIn('verdeckt', caption.cget('text'))
                    else:
                        self.assertNotIn('verdeckt', caption.cget('text'))
