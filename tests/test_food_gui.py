"""Real Tk selection and frame-anchored food PNG overlays."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.presentation.food_models import food_choices


class FoodGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Tk display unavailable") from error
        root.destroy()

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.pet = DesktopPet(store=StateStore(Path(temp.name) / "pet.json"))
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        self.pet.state.sleeping = False
        self.pet._on_enter()

    def test_selecting_one_of_five_foods_feeds_the_matching_item(self) -> None:
        bar = self.pet._hover.toolbar
        assert bar is not None
        bar.buttons["feed"].invoke()
        menu = self.pet._hover.food_menu
        assert menu is not None
        self.assertEqual(
            set(menu.buttons),
            {"onigiri", "sandwich", "taiyaki", "apple", "dango"},
        )
        self.assertEqual(len(menu.images), 5)
        self.assertEqual(self.pet.state.satiety, 75)
        menu.buttons["apple"].invoke()
        self.assertIsNone(self.pet._hover.food_menu)
        self.assertEqual(self.pet.state.food.last_food_id, "apple")
        self.assertEqual(self.pet._animated.food_overlay.current_food_id, "apple")
        self.assertAlmostEqual(self.pet.state.satiety, 89, places=2)

    def test_same_menu_instance_is_focused_instead_of_duplicated(
        self,
    ) -> None:
        self.pet._hover.open_food_menu()
        first = self.pet._hover.food_menu
        assert first is not None
        self.pet._hover.open_food_menu()
        self.assertIs(self.pet._hover.food_menu, first)
        first.close()
        self.assertIsNone(self.pet._hover.food_menu)

    def test_png_assets_are_64_pixels_and_have_alpha(self) -> None:
        choices = food_choices()
        self.assertEqual(len(choices), 5)
        for choice in choices:
            with self.subTest(food=choice.id):
                self.assertEqual(
                    choice.image_path.parent, ASSET_ROOT / "food",
                )
                self.assertTrue(choice.image_path.is_file())
                image = tk.PhotoImage(
                    master=self.pet.root, file=str(choice.image_path),
                )
                self.assertEqual((image.width(), image.height()), (64, 64))
                self.assertTrue(image.transparency_get(0, 0))

    def test_hand_overlay_uses_the_eight_authored_frame_anchors(self) -> None:
        animated = self.pet._animated
        clip = animated.assets.clips["eat"]
        self.assertEqual(len(clip.frames), 8)
        self.assertTrue(all(frame.food_anchor is not None for frame in clip.frames))
        animated.set_food_overlay("sandwich")
        animated.begin_action("eat", time.monotonic())
        overlay = animated.food_overlay
        self.assertEqual(self.pet.canvas.itemcget(overlay.item, "state"), "normal")
        positions: list[tuple[float, ...]] = []
        for index, frame in enumerate(clip.frames):
            animated.show_frame("eat", time.monotonic(), fixed=index)
            positions.append(tuple(self.pet.canvas.coords(overlay.item)))
            self.assertEqual(self.pet.canvas.itemcget(overlay.item, "state"),
                             "normal")
            self.assertIsNotNone(frame.food_anchor)
        self.assertGreater(len(set(positions)), 2)
        animated.show_frame("idle", time.monotonic(), fixed=0)
        self.assertEqual(self.pet.canvas.itemcget(overlay.item, "state"), "hidden")


if __name__ == "__main__":
    unittest.main()
