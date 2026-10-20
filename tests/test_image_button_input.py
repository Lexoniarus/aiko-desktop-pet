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

    def click_child(self, widget):
        widget.event_generate("<Enter>")
        widget.event_generate("<ButtonPress-1>", x=2, y=2)
        widget.event_generate("<ButtonRelease-1>", x=2, y=2)
        self.root.update()

    def test_text_and_chevron_invoke_once_and_respect_disabled_state(self):
        for label in (self.button._copy, self.button._chevron):
            assert label is not None
            with self.subTest(child=str(label)):
                self.calls.clear()
                self.click_child(label)
                self.assertEqual(self.calls, ["choose"])
                self.button.configure(state="disabled")
                self.click_child(label)
                self.assertEqual(self.calls, ["choose"])
                self.button.configure(state="normal")

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


if __name__ == "__main__":
    unittest.main()
