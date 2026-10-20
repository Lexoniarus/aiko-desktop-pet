"""Single-window VN rendering, native input and repeated scrolling."""

import tkinter as tk
import unittest

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.view_models.food_models import food_choices
from aiko_pet.ui.windows.food_menu import FoodMenu


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
        self.button.event_generate("<ButtonPress-1>", x=2, y=2)
        self.root.update()
        self.assertEqual(self.calls, ["place"])
        self.assertFalse(self.button.winfo_exists())
        self.assertEqual(errors, [])

    def test_stacked_choice_is_one_widget_and_respects_disabled_input(self):
        button = self.skin.button(
            self.root, "Stein", lambda: self.calls.append("stone"),
            size="game_choice", icon=self.skin.images.icon("play_rps_rock", 64),
            stacked=True,
        )
        button.pack()
        self.root.update()
        self.assertEqual(button.winfo_children(), [])
        button.event_generate("<Enter>", x=20, y=20)
        button.event_generate("<ButtonPress-1>", x=20, y=20)
        button.event_generate("<ButtonRelease-1>", x=20, y=20)
        self.root.update()
        self.assertEqual(self.calls, ["stone"])
        button.configure(state="disabled")
        self.assertTrue(button.instate(["disabled"]))
        button.event_generate("<ButtonPress-1>", x=20, y=20)
        button.event_generate("<ButtonRelease-1>", x=20, y=20)
        self.root.update()
        self.assertEqual(self.calls, ["stone"])

    def test_selection_survives_native_hover_press_and_disabling(self):
        button = self.button
        button.set_selected(True)
        for event in ("<Enter>", "<ButtonPress-1>", "<ButtonRelease-1>", "<Leave>"):
            button.event_generate(event, x=5, y=5)
            self.assertTrue(button.instate(["selected"]))
        button.configure(state="disabled")
        self.assertTrue(button.instate(["selected", "disabled"]))
        self.assertEqual(self.skin.images.buttons.style.lookup(
            button.cget("style"), "foreground", state=button.state(),
        ), "#817883")
        button.configure(state="normal")
        self.assertTrue(button.instate(["selected", "!disabled"]))

    def test_snack_scroll_and_reopen_keep_icons_and_native_text_together(self):
        host = tk.Frame(self.root)
        host.pack()
        choices = food_choices(load_item_catalog())

        def open_menu():
            menu = FoodMenu(
                host, choices=choices, selected=lambda _key: None,
                closed=lambda: None, skin=self.skin, can_select=lambda: True,
            )
            self.addCleanup(menu.close)
            self.root.update()
            return menu

        menu = open_menu()
        expected = {
            key: (button.cget("text"), button.cget("image"), button.cget("style"))
            for key, button in menu.buttons.items()
        }
        count = len(self.skin.images.buttons._styles)
        for position in (1, 0, 0.5, 0, 1, 0):
            menu.scroll.canvas.yview_moveto(position)
            self.root.update()
            for key, button in menu.buttons.items():
                self.assertEqual(button.winfo_children(), [])
                self.assertEqual(button.tk.call(str(button), "cget", "-text"),
                                 expected[key][0])
                self.assertEqual(button.cget("image"), expected[key][1])
                self.assertEqual(button.cget("style"), expected[key][2])
        menu.close()
        reopened = open_menu()
        self.assertEqual(len(self.skin.images.buttons._styles), count)
        for key, button in reopened.buttons.items():
            self.assertEqual(button.winfo_children(), [])
            self.assertEqual(button.cget("style"), expected[key][2])


if __name__ == "__main__":
    unittest.main()
