"""Real Tk food-menu selection and cursor custody."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from tools.pet_test_support import set_test_pet_values


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
        set_test_pet_values(self.pet.state, sleeping=False)
        self.pet._hover.show_toolbar()

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
        token = self.pet._world.cursor.instance_id
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

    def test_energy_drink_selection_carries_without_awarding_energy(self) -> None:
        bar = self.pet._hover.toolbar
        assert bar is not None
        set_test_pet_values(self.pet.state, energy=40)
        set_test_pet_values(self.pet.state, satiety=30)
        old_fun = self.pet.state.fun
        old_food_history = self.pet.state.food.recent_food_ids
        bar.buttons["feed"].invoke()
        menu = self.pet._hover.food_menu
        assert menu is not None
        self.assertEqual(menu.buttons["energy_drink"].cget("text"), "Energy Drink")
        # Gesture start now saves through the active-time owner. Isolate the
        # selection effect from real elapsed need decay in this boundary test.
        with patch("aiko_pet.application.active_time.ActiveSessionClock.consume",
                   return_value=0):
            menu.buttons["energy_drink"].invoke()
        self.assertIsNone(self.pet._hover.food_menu)
        self.assertEqual(self.pet.state.energy, 40)
        self.assertLess(self.pet.state.satiety, 40)
        self.assertEqual(
            self.pet.state.food.recent_food_ids, old_food_history,
        )
        self.assertEqual(self.pet.state.food.remaining_digest_minutes, 0)
        self.assertAlmostEqual(self.pet.state.fun, old_fun, places=1)
        token = self.pet._world.cursor.instance_id
        assert token is not None
        self.assertEqual(self.pet._world.world.get(token).definition_id, "energy_drink")
        self.assertIsNone(self.pet._animated.food_overlay.current_food_id)

    def test_full_energy_rejects_drink_without_eating_animation(self) -> None:
        set_test_pet_values(self.pet.state, energy=100)
        set_test_pet_values(self.pet.state, satiety=45)
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


if __name__ == "__main__":
    unittest.main()
