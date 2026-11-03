"""Native menu geometry, overflow and prepared-art integration without a save."""

from __future__ import annotations

import tkinter as tk
import unittest
from dataclasses import replace
from unittest.mock import Mock

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.games.contracts import GameId
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletState
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishId, WishState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.view_models.contracts import HoverAnchor
from aiko_pet.ui.view_models.projections import project_hover, project_status
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.game_menu import GameMenu
from aiko_pet.ui.windows.hover_contracts import HoverActions


class MainMenuLayoutTests(unittest.TestCase):
    def test_every_action_has_full_visible_bounds_and_accepts_native_clicks(self):
        for action, button in self.toolbar.buttons.items():
            with self.subTest(action=action):
                self.toolbar.tips.hide()
                self.root.update_idletasks()
                self.assertGreaterEqual(button.winfo_width(),
                                        button.winfo_reqwidth())
                self.assertGreaterEqual(button.winfo_height(),
                                        button.winfo_reqheight())
                x, y = button.winfo_rootx(), button.winfo_rooty()
                ancestor = button.master
                while ancestor is not self.toolbar.window:
                    assert ancestor is not None
                    self.assertGreaterEqual(x, ancestor.winfo_rootx())
                    self.assertGreaterEqual(y, ancestor.winfo_rooty())
                    self.assertLessEqual(
                        x + button.winfo_width(),
                        ancestor.winfo_rootx() + ancestor.winfo_width(),
                    )
                    self.assertLessEqual(
                        y + button.winfo_height(),
                        ancestor.winfo_rooty() + ancestor.winfo_height(),
                    )
                    ancestor = ancestor.master
                self.calls.clear()
                for event in ('<Enter>', '<ButtonPress-1>', '<ButtonRelease-1>'):
                    button.event_generate(event, x=button.winfo_width() // 2,
                                          y=button.winfo_height() // 2)
                self.root.update()
                self.assertEqual(self.calls, [action])

    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Native Tk display required") from error
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.skin = AikoSkin(self.root)
        self.state = PetState(
            moodlets=MoodletState(active=tuple(
                MoodletEpisode(i, key, 1, 0, 0, 7200)
                for i, key in enumerate(tuple(MOODLET_CATALOG.definitions)[:4], 1)
            )),
            wishes=WishState(active=(
                ActiveWish(1, WishId.PLAY_GAME, "tic_tac_toe", 0, 14400),
                ActiveWish(2, WishId.FACT, "fact", 0, 14400),
                ActiveWish(3, WishId.PET, "pet", 0, 14400),
            )),
        )
        read = snapshot_pet(self.state)
        context = context_at(1_800_000_000)
        self.view = project_hover(
            read, context, ComputerSnapshot(), observe_computer=False,
        )
        self.calls: list[str] = []
        self.toolbar = ActionToolbar(
            self.root, snapshot=lambda: self.view,
            status_snapshot=lambda: project_status(
                read, context, None, ComputerSnapshot(), observe_computer=False,
            ),
            anchor=lambda: HoverAnchor(100, 100, 192, 208, None, None),
            actions=HoverActions(
                self.calls.append, Mock(), Mock(), Mock(), Mock(), lambda: True,
            ),
            always_on_top=False, skin=self.skin,
        )
        self.addCleanup(self.toolbar.close)
        self.toolbar.set_pinned(False)
        self.toolbar.show()
        self.root.update()

    def test_three_wishes_fit_and_empty_rows_release_space(self) -> None:
        wishes = self.toolbar.wishes._content
        width = self.toolbar.window.winfo_width()
        for pinned in (False, True, False):
            with self.subTest(pinned=pinned):
                self.view = replace(self.view, emotional=replace(
                    self.view.emotional, wishes=tuple(
                        replace(item, value=replace(item.value, pinned=pinned))
                        for item in self.view.emotional.wishes
                    ),
                ))
                self.toolbar.refresh()
                self.root.update()
                self.assertEqual(self.toolbar.window.winfo_width(), width)
                self.assertFalse(hasattr(wishes, "scrollbar"))
                self.assertLessEqual(wishes.body.winfo_reqwidth(),
                                     wishes.frame.winfo_width())
                for key, label in self.toolbar.wishes._labels.items():
                    pin = self.toolbar.wishes._pin_icons[key]
                    objective = self.toolbar.wishes._objectives[key]
                    self.assertEqual(pin.itemcget("pin", "state"),
                                     "normal" if pinned else "hidden")
                    self.assertLessEqual(label.winfo_x() + label.winfo_width(),
                                         pin.winfo_x())
                    self.assertLessEqual(pin.winfo_y() + pin.winfo_height(),
                                         objective.winfo_y())
        for label in self.toolbar.wishes._meta.values():
            self.assertLessEqual(
                label.winfo_y() + label.winfo_height(),
                label.master.winfo_height(),
            )
        populated = self.toolbar.window.winfo_height()
        self.view = replace(self.view, emotional=replace(
            self.view.emotional, wishes=(), moodlets=(),
        ))
        self.toolbar.refresh()
        self.root.update()
        self.assertLess(self.toolbar.window.winfo_height(), populated)
        self.assertFalse(hasattr(self.toolbar.moodlets._content, "scrollbar"))

    def test_selector_retains_geometry_and_uses_panel_art(self) -> None:
        before = self.toolbar.window.winfo_geometry()
        menu = GameMenu(
            self.toolbar.selector_parent(lambda _reason: None), choices=tuple(GameId),
            selected=Mock(), closed=Mock(), skin=self.skin, can_select=lambda: True,
        )
        self.addCleanup(menu.close)
        self.root.update()
        self.assertEqual(self.toolbar.window.winfo_width(), int(before.split("x")[0]))
        self.assertIs(menu.content.frame.ui_scale, self.skin.scale)
        self.assertIsNotNone(menu._surface._image)
        # The entire selector grows naturally; every choice remains visible.
        self.root.update()
        last = menu.buttons[GameId.MASTERMIND]
        self.assertGreaterEqual(last.winfo_rooty(), menu.content.frame.winfo_rooty())
        self.assertLessEqual(
            last.winfo_rooty() + last.winfo_height(),
            menu.content.frame.winfo_rooty() + menu.content.frame.winfo_height(),
        )
        for button in menu.buttons.values():
            self.assertLessEqual(
                button.winfo_width(), menu.content.frame.winfo_width(),
            )

    def test_many_moodlets_wrap_without_a_scroll_view(self) -> None:
        episodes = tuple(
            MoodletEpisode(i, key, 1, 0, 0, 7200)
            for i, key in enumerate(MOODLET_CATALOG.definitions, 1)
        )
        state = PetState(moodlets=MoodletState(active=episodes))
        overflow = project_hover(
            snapshot_pet(state), context_at(1_800_000_000), ComputerSnapshot(),
            observe_computer=False,
        )
        self.view = overflow
        self.toolbar.refresh()
        strip = self.toolbar.moodlets._content
        self.root.update()
        self.assertFalse(hasattr(strip, "scrollbar"))
        self.assertEqual(strip.frame.ui_scale, self.skin.scale)
        self.view = replace(
            overflow, emotional=replace(overflow.emotional, moodlets=()),
        )
        self.toolbar.refresh()
        self.root.update()
        self.assertFalse(hasattr(strip, "scrollbar"))

    def test_details_are_bounded_and_button_copy_keeps_native_commands(self) -> None:
        self.toolbar.toggle_details()
        self.root.update()
        self.assertLessEqual(
            self.toolbar.window.winfo_height(), self.root.winfo_screenheight(),
        )
        details = self.toolbar.details
        assert details is not None
        self.assertIsNotNone(details._surface._image)
        button = self.toolbar.buttons["pet"]
        self.assertEqual(button.winfo_children(), [])
        self.assertEqual(
            button.tk.call(str(button), "cget", "-text"), button.cget("text"),
        )
        button.configure(state="disabled")
        button.invoke()
        self.assertEqual(self.calls, [])
        button.configure(state="normal")
        button.invoke()
        self.assertEqual(self.calls, ["pet"])
        button.configure(text="Test ›")
        self.assertEqual(button.cget("text"), "Test ›")
        self.assertEqual(button.tk.call(str(button), "cget", "-text"), "Test")

    def test_panel_resizing_preserves_corners_without_growing_cache(self) -> None:
        source = self.skin.images.surface("panel_surface.panel")
        painted = self.skin.scale.image(source)
        sw = int(self.root.tk.call('image', 'width', painted))
        sh = int(self.root.tk.call('image', 'height', painted))
        cache_size = len(self.skin.images._images)
        for width, height in ((74, 30), (254, 354), (620, 228)):
            image = self.skin.images.panel_art(width, height)
            self.assertEqual(image.get(1, 1), self.root.tk.call(painted, 'get', 1, 1))
            self.assertEqual(
                image.get(width - 2, height - 2),
                self.root.tk.call(painted, 'get', sw - 2, sh - 2),
            )
        self.assertEqual(len(self.skin.images._images), cache_size)

    def test_details_and_footer_use_the_shared_scale_without_viewports(self):
        self.toolbar.toggle_details()
        self.root.update()
        self.assertFalse(hasattr(self.toolbar.body, 'canvas'))
        self.assertTrue(self.toolbar.pin_button.winfo_ismapped())
        self.assertTrue(self.toolbar.details_button.winfo_ismapped())
        self.assertIs(self.toolbar.details_button.ui_scale, self.skin.scale)

    def test_entire_button_uses_one_native_pointer_and_disabled_gate(self) -> None:
        button = self.toolbar.buttons["pet"]
        for x in (8, 80, button.winfo_width() - 18):
            with self.subTest(x=x):
                self.calls.clear()
                for state, expected in (("disabled", []), ("normal", ["pet"])):
                    button.configure(state=state)
                    for sequence in ("<Enter>", "<ButtonPress-1>", "<ButtonRelease-1>"):
                        button.event_generate(sequence, x=x, y=15)
                    self.root.update()
                    self.assertEqual(self.calls, expected)


if __name__ == "__main__":
    unittest.main()
