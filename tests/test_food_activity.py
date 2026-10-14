"""Anonymous measured activity for hunger: CPU/GPU/RAM and real inputs."""

from __future__ import annotations

import unittest
from dataclasses import fields

from aiko_pet.application.food_activity import FoodActivityHistory


class FoodActivityHistoryTests(unittest.TestCase):
    def test_actual_pointer_input_and_hardware_each_count_independently(
        self,
    ) -> None:
        history = FoodActivityHistory()
        for i in range(90):
            history.observe(
                now=1000.0 + i,
                pointer=(i * 12, 15),
                input_idle_seconds=0.1,
                mouse_buttons_down=(False, False),
                measured_hardware_load=0.9,
            )
        view = history.current_food_activity(1100.0)
        self.assertGreater(view.hardware_load, 0.8)
        self.assertGreater(view.user_input_activity, 0.8)

    def test_load_without_user_input_is_work_but_not_user_activity(
        self,
    ) -> None:
        history = FoodActivityHistory()
        for i in range(30):
            history.observe(
                now=100.0 + i,
                pointer=(500, 500),
                input_idle_seconds=300.0,
                mouse_buttons_down=(False, False),
                measured_hardware_load=1.0,
            )
        view = history.current_food_activity(130.0)
        self.assertGreater(view.hardware_load, 0.9)
        self.assertEqual(view.user_input_activity, 0)

    def test_active_inputs_with_idle_cpu_still_count_as_user_activity(
        self,
    ) -> None:
        history = FoodActivityHistory()
        for i in range(30):
            history.observe(
                now=100.0 + i,
                pointer=(200, 200),
                input_idle_seconds=0.1,
                mouse_buttons_down=(False, False),
                measured_hardware_load=0.05,
            )
        view = history.current_food_activity(130.0)
        self.assertGreater(view.user_input_activity, 0.70)
        self.assertLess(view.hardware_load, 0.10)

    def test_one_idle_pointer_sighting_does_not_claim_an_hour_of_work(
        self,
    ) -> None:
        history = FoodActivityHistory()
        history.observe(
            now=10.0, pointer=(1, 1), input_idle_seconds=0.1,
            mouse_buttons_down=None, measured_hardware_load=None,
        )
        history.observe(
            now=11.0, pointer=(1, 1), input_idle_seconds=100.0,
            mouse_buttons_down=None, measured_hardware_load=None,
        )
        self.assertEqual(
            history.current_food_activity(12.0).user_input_activity, 0.0,
        )
        history.observe(
            now=9000.0, pointer=(1, 1), input_idle_seconds=8000.0,
            mouse_buttons_down=None, measured_hardware_load=None,
        )
        self.assertEqual(
            history.current_food_activity(9000.0).hardware_load, 0.0,
        )

    def test_synthetic_long_sampling_gap_does_not_create_work(
        self,
    ) -> None:
        history = FoodActivityHistory()
        history.observe(
            now=100, pointer=(0, 0), input_idle_seconds=0,
            mouse_buttons_down=None, measured_hardware_load=1,
        )
        history.observe(
            now=200, pointer=(900, 900), input_idle_seconds=0,
            mouse_buttons_down=None, measured_hardware_load=1,
        )
        self.assertEqual(
            history.current_food_activity(200).hardware_load, 0.0,
        )

    def test_input_signals_never_store_sensitive_event_content(
        self,
    ) -> None:
        history = FoodActivityHistory()
        history.observe(
            now=10, pointer=(123, 456), input_idle_seconds=0.2,
            mouse_buttons_down=(False, False),
            measured_hardware_load=0.4,
        )
        history.observe(
            now=11, pointer=(125, 456), input_idle_seconds=0.3,
            mouse_buttons_down=(True, False),
            measured_hardware_load=0.4,
        )
        self.assertGreater(
            history.current_food_activity(12).user_input_activity, 0,
        )
        self.assertFalse(hasattr(history, "keystrokes"))
        self.assertFalse(hasattr(history, "raw_events"))
        self.assertEqual(
            {field.name for field in fields(history._buckets[-1])},
            {"index", "observed_seconds", "user_active_seconds",
             "hardware_work_seconds"},
        )


if __name__ == "__main__":
    unittest.main()
