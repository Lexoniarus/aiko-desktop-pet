"""Real Tk selection and frame-anchored food PNG overlays."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.view_models.food_models import food_choices


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

    def test_selecting_from_eleven_foods_carries_without_feeding(self) -> None:
        bar = self.pet._hover.toolbar
        assert bar is not None
        bar.buttons["feed"].invoke()
        menu = self.pet._hover.food_menu
        assert menu is not None
        self.assertEqual(
            set(menu.buttons),
            {"onigiri", "sandwich", "taiyaki", "apple", "dango",
             "donut", "cookie", "melonpan", "cupcake", "dorayaki",
             "energy_drink"},
        )
        self.assertEqual(len(menu.images), 11)
        self.assertEqual(menu.columns, 6)
        self.assertEqual(self.pet.state.satiety, 75)
        menu.buttons["apple"].invoke()
        self.assertIsNone(self.pet._hover.food_menu)
        token = self.pet._world.carry_id
        assert token is not None
        self.assertEqual(self.pet._world.world.get(token).definition_id, "apple")
        self.assertIsNone(self.pet.state.food.last_food_id)
        self.assertIsNone(self.pet._animated.food_overlay.current_food_id)
        self.assertAlmostEqual(self.pet.state.satiety, 75, places=2)

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
        choices = food_choices(self.pet._item_catalog)
        self.assertEqual(len(choices), 11)
        for choice in choices:
            with self.subTest(food=choice.id):
                self.assertEqual(
                    choice.image_path.parent,
                    ASSET_ROOT / "items" / "icons" / "64",
                )
                self.assertTrue(choice.image_path.is_file())
                image = tk.PhotoImage(
                    master=self.pet.root, file=str(choice.image_path),
                )
                self.assertEqual((image.width(), image.height()), (64, 64))
                self.assertTrue(image.transparency_get(0, 0))

    def test_energy_drink_selection_carries_without_awarding_energy(self) -> None:
        bar = self.pet._hover.toolbar
        assert bar is not None
        self.pet.state.energy = 40
        self.pet.state.satiety = 30
        old_fun = self.pet.state.fun
        old_food_history = self.pet.state.food.recent_food_ids
        bar.buttons["feed"].invoke()
        menu = self.pet._hover.food_menu
        assert menu is not None
        self.assertEqual(menu.buttons["energy_drink"].cget("text"), "Energy Drink")
        menu.buttons["energy_drink"].invoke()
        self.assertIsNone(self.pet._hover.food_menu)
        self.assertEqual(self.pet.state.energy, 40)
        self.assertLess(self.pet.state.satiety, 40)
        self.assertEqual(
            self.pet.state.food.recent_food_ids, old_food_history,
        )
        self.assertEqual(self.pet.state.food.remaining_digest_minutes, 0)
        self.assertAlmostEqual(self.pet.state.fun, old_fun, places=1)
        token = self.pet._world.carry_id
        assert token is not None
        self.assertEqual(self.pet._world.world.get(token).definition_id, "energy_drink")
        self.assertIsNone(self.pet._animated.food_overlay.current_food_id)

    def test_full_energy_rejects_drink_without_eating_animation(self) -> None:
        self.pet.state.energy = 100
        self.pet.state.satiety = 45
        self.pet._hover.open_food_menu()
        menu = self.pet._hover.food_menu
        assert menu is not None
        with patch.object(
            self.pet.application._care._clock, "consume",
            return_value=0.0,
        ):
            menu.buttons["energy_drink"].invoke()
        self.assertIsNone(self.pet._animated.food_overlay.current_food_id)
        self.assertNotEqual(
            self.pet._animated.frame_clock.active_key, ("eat", None),
        )

    def test_all_native_food_overlays_render_at_both_scales(self) -> None:
        overlay = self.pet._animated.food_overlay
        for scale in (1, 2):
            self.pet.settings.scale = scale
            self.pet._window.resize()
            self.pet._animated.reload_sprites()
            for choice in food_choices(self.pet._item_catalog):
                with self.subTest(scale=scale, food=choice.id):
                    self.pet._animated.set_food_overlay(choice.id)
                    self.pet._animated.begin_action("eat", time.monotonic())
                    self.assertEqual(
                        self.pet.canvas.itemcget(overlay.item, "state"),
                        "normal",
                    )
                    expected = overlay._images[(choice.id, scale)]
                    sprite = self.pet._item_catalog.foods[choice.id].sprites[scale]
                    self.assertEqual(expected.cget("file"), str(sprite.render_path))
                    self.assertEqual(
                        self.pet._world.view.image(choice.id, scale).cget("file"),
                        str(sprite.render_path),
                    )
                    actual = self.pet.canvas.itemcget(overlay.item, "image")
                    self.assertEqual(actual, str(expected))
                    self.pet._animated.show_frame(
                        "idle", time.monotonic(), fixed=0,
                    )
                    self.assertEqual(
                        self.pet.canvas.itemcget(overlay.item, "state"),
                        "hidden",
                    )

    def test_switching_scale_does_not_interrupt_animation_timers(self) -> None:
        self.pet._animated.set_food_overlay("cupcake")
        self.pet._animated.begin_action("eat", time.monotonic())
        clock = self.pet._animated.frame_clock
        for scale in (2, 1, 2):
            self.pet.settings.scale = scale
            self.pet._window.resize()
            self.pet._animated.reload_sprites()
            self.assertIs(self.pet._animated.frame_clock, clock)
            self.assertEqual(
                self.pet._animated.food_overlay.current_food_id, "cupcake",
            )
            self.assertIsNotNone(self.pet._animated._frame_timer)

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
