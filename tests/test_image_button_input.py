"""Native VN label forwarding preserves one command and disabled boundaries."""

import tkinter as tk
import unittest

from aiko_pet.ui.common.skin import AikoSkin


class ImageButtonInputTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Native Tk display required") from error
        self.addCleanup(self.root.destroy)
        self.calls = []
        self.skin = AikoSkin(self.root)
        self.button = self.skin.button(
            self.root, "Auswahl  ›", lambda: self.calls.append("choose"),
            align_left=True,
        )
        self.button.pack()
        self.root.update()

    def test_keyboard_stays_on_the_native_button_after_text_updates(self):
        self.button.configure(text="Neue Auswahl  ›")
        self.button.focus_force()
        self.root.update()
        self.button.event_generate("<Return>")
        self.root.update()
        self.assertEqual(self.calls, ["choose"])
        self.button.configure(state="disabled")
        self.button.event_generate("<Return>")
        self.root.update()
        self.assertEqual(self.calls, ["choose"])

    def test_press_can_close_selector_before_release_without_duplicate_command(self):
        errors = []
        self.root.report_callback_exception = lambda *_args: errors.append(_args[1])

        def choose(_event):
            self.calls.append("place")
            self.button.destroy()
            return "break"

        self.button.bind("<ButtonPress-1>", choose)
        label = self.button._copy
        assert label is not None
        label.event_generate("<ButtonPress-1>", x=2, y=2)
        self.root.update()
        self.assertEqual(self.calls, ["place"])
        self.assertFalse(self.button.winfo_exists())
        self.assertEqual(errors, [])

    def test_stacked_choice_art_forwards_once_and_respects_disabled_input(self):
        button = self.skin.button(
            self.root, "Stein", lambda: self.calls.append("stone"),
            size="game_choice", icon=self.skin.images.icon("play_rps_rock", 64),
            stacked=True,
        )
        button.pack()
        self.root.update()
        face = button._face
        assert face is not None
        face.event_generate("<Enter>", x=20, y=20)
        face.event_generate("<ButtonPress-1>", x=20, y=20)
        face.event_generate("<ButtonRelease-1>", x=20, y=20)
        self.root.update()
        self.assertEqual(self.calls, ["stone"])
        button.configure(state="disabled")
        self.assertEqual(face.cget("image"), str(button._art["disabled"]))
        face.event_generate("<ButtonPress-1>", x=20, y=20)
        face.event_generate("<ButtonRelease-1>", x=20, y=20)
        self.root.update()
        self.assertEqual(self.calls, ["stone"])


if __name__ == "__main__":
    unittest.main()
