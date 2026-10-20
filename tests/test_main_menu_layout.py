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
        wishes = self.toolbar.wishes._scroll
        self.assertFalse(wishes.scrollbar.winfo_ismapped())
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
        self.assertFalse(self.toolbar.moodlets._scroll.scrollbar.winfo_ismapped())

    def test_selector_retains_geometry_and_uses_panel_art(self) -> None:
        before = self.toolbar.window.winfo_geometry()
        menu = GameMenu(
            self.toolbar.selector_parent(lambda: None), choices=tuple(GameId),
            selected=Mock(), closed=Mock(), skin=self.skin, can_select=lambda: True,
        )
        self.addCleanup(menu.close)
        self.root.update()
        self.assertEqual(self.toolbar.window.winfo_geometry(), before)
        self.assertIsNotNone(menu._surface._image)
        self.assertFalse(menu.scroll.scrollbar.winfo_ismapped())
        for button in menu.buttons.values():
            self.assertLessEqual(
                button.winfo_width(), menu.scroll.canvas.winfo_width(),
            )

    def test_overflow_can_be_scrolled_and_hides_bar_after_removal(self) -> None:
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
        strip = self.toolbar.moodlets._scroll
        self.root.update()
        self.assertTrue(strip.scrollbar.winfo_ismapped())
        strip.canvas.xview_moveto(1)
        self.assertGreater(strip.canvas.xview()[0], 0)
        self.view = replace(
            overflow, emotional=replace(overflow.emotional, moodlets=()),
        )
        self.toolbar.refresh()
        self.root.update()
        self.assertFalse(strip.scrollbar.winfo_ismapped())
        self.assertEqual(strip.canvas.xview()[0], 0)

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
        assert button._copy is not None and button._chevron is not None
        self.assertEqual(button._copy.cget("text"), button.cget("text"))
        button.configure(state="disabled")
        button.invoke()
        self.assertEqual(self.calls, [])
        button.configure(state="normal")
        button.invoke()
        self.assertEqual(self.calls, ["pet"])
        button.configure(text="Test ›")
        self.assertEqual(button.cget("text"), "Test ›")
        self.assertEqual(button._copy.cget("text"), "Test")
        self.assertEqual(button._chevron.cget("text"), "›")

    def test_panel_resizing_preserves_corners_without_growing_cache(self) -> None:
        source = self.skin.images.surface("panel_surface.panel")
        cache_size = len(self.skin.images._images)
        for width, height in ((74, 30), (254, 354), (620, 228)):
            image = self.skin.images.panel_art(width, height)
            self.assertEqual(image.get(1, 1), source.get(1, 1))
            self.assertEqual(
                image.get(width - 2, height - 2),
                source.get(source.width() - 2, source.height() - 2),
            )
        self.assertEqual(len(self.skin.images._images), cache_size)

    def test_short_viewport_reveals_details_and_preserves_footer_access(self) -> None:
        self.toolbar.body._max_height = 380
        self.toolbar.body.refresh_layout()
        self.root.update()
        self.toolbar.toggle_details()
        self.root.update()
        self.assertLessEqual(self.toolbar.body.canvas.winfo_height(), 380)
        self.assertAlmostEqual(self.toolbar.body.canvas.yview()[1], 1)
        self.assertTrue(self.toolbar.pin_button.winfo_ismapped())
        self.assertTrue(self.toolbar.details_button.winfo_ismapped())

    def test_label_pointer_events_use_the_native_button_and_disabled_gate(self) -> None:
        button = self.toolbar.buttons["pet"]
        for label in (button._copy, button._chevron):
            assert label is not None
            with self.subTest(child=str(label)):
                self.calls.clear()
                for state, expected in (("disabled", []), ("normal", ["pet"])):
                    button.configure(state=state)
                    for sequence in ("<Enter>", "<ButtonPress-1>", "<ButtonRelease-1>"):
                        label.event_generate(sequence, x=5, y=5)
                    self.root.update()
                    self.assertEqual(self.calls, expected)


if __name__ == "__main__":
    unittest.main()
