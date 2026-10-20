"""Real Tk food-menu selection and cursor custody."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.world.contracts import ObjectState
from tools.desktop_test_support import create_test_desktop
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
        self.pet = create_test_desktop(store=StateStore(Path(temp.name) / "pet.json"))
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        set_test_pet_values(self.pet.state, sleeping=False)
        self.pet._hover.show_toolbar()

    def test_selecting_from_eleven_foods_carries_without_feeding(self) -> None:
        bar = self.pet._hover.toolbar
        assert bar is not None
        bar.buttons["place_item"].invoke()
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
        # Menu selection starts a gesture at either capacity. Refusal requires
        # later hand/face evidence and is covered by World interaction tests.
        with patch("aiko_pet.application.active_time.ActiveSessionClock.consume",
                   return_value=0):
            for energy in (40, 100):
                with self.subTest(energy=energy):
                    set_test_pet_values(self.pet.state, energy=energy, satiety=30)
                    old_fun = self.pet.state.fun
                    old_friendship = self.pet.state.friendship
                    old_food_history = self.pet.state.food.recent_food_ids
                    self.assertFalse(self.pet._world.cursor.carrying)
                    bar.buttons["place_item"].invoke()
                    menu = self.pet._hover.food_menu
                    assert menu is not None
                    self.assertEqual(menu.buttons["energy_drink"].cget("text"),
                                     "Energy Drink")
                    menu.buttons["energy_drink"].invoke()
                    self.assertIsNone(self.pet._hover.food_menu)
                    token = self.pet._world.cursor.instance_id
                    assert token is not None
                    item = self.pet._world.world.get(token)
                    self.assertEqual(item.definition_id, "energy_drink")
                    self.assertEqual(item.state, ObjectState.USER_HELD)
                    self.assertEqual(self.pet._world.interaction.phase, "idle")
                    self.assertEqual(self.pet.state.energy, energy)
                    self.assertEqual(self.pet.state.satiety, 30)
                    self.assertEqual(self.pet.state.food.recent_food_ids,
                                     old_food_history)
                    self.assertEqual(self.pet.state.food.remaining_digest_minutes, 0)
                    self.assertEqual(self.pet.state.fun, old_fun)
                    self.assertEqual(self.pet.state.friendship, old_friendship)
                    self.assertIsNone(self.pet._animated.food_overlay.current_food_id)
                    self.assertNotEqual(self.pet._animated.frame_clock.active_key,
                                        ("eat", None))
                    self.pet._world.cursor.cancel()


if __name__ == "__main__":
    unittest.main()
