"""Anonymous measured activity for hunger: CPU/GPU/RAM and real inputs."""

from __future__ import annotations

import unittest
from dataclasses import fields
from datetime import datetime

from aiko_pet.application.food_activity import FoodActivityHistory
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.lifecycle import MAX_LIVE_EFFORT_SECONDS
from aiko_pet.pet.state import PetState


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


def bond_stamp(day: str = "2026-10-12", hour: int = 12) -> float:
    return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone().timestamp()


class TelemetryEffortTests(unittest.TestCase):
    def test_high_work_only_adds_bounded_hunger_and_energy_costs(self):
        start = bond_stamp()
        calm = PetState(updated_at=start, friendship=40)
        busy = PetState(updated_at=start, friendship=40)
        for step in range(1, 361):
            point = start + step * 10
            calm.advance(point, effort=0.05)
            busy.advance(point, effort=1.0)
        self.assertAlmostEqual(calm.satiety - busy.satiety, 1.6)
        self.assertAlmostEqual(calm.energy - busy.energy, 0.5)
        self.assertAlmostEqual(calm.mood - busy.mood, 0.16 * (1.6 + 0.5))
        self.assertAlmostEqual(calm.social, busy.social)
        self.assertAlmostEqual(calm.affection, busy.affection)
        self.assertAlmostEqual(calm.fun, busy.fun)
        self.assertAlmostEqual(busy.friendship, calm.friendship)
        self.assertGreater(busy.friendship, 39.99)
        self.assertLessEqual(busy.friendship, 40)

    def test_observed_load_cannot_be_extrapolated_over_offline_hours(self):
        start = bond_stamp()
        base = PetState(updated_at=start)
        busy = PetState(updated_at=start)
        base.advance(start + 8 * 3600)
        busy.advance(start + 8 * 3600, effort=1.0)
        self.assertLess(base.satiety - busy.satiety, 0.1)
        self.assertLess(base.mood - busy.mood, 0.1)
        self.assertLess(base.energy - busy.energy, 0.1)
        self.assertEqual(MAX_LIVE_EFFORT_SECONDS, 30)

    def test_missing_and_invalid_telemetry_use_normal_decay(self):
        start = bond_stamp()
        state_a = PetState(updated_at=start)
        state_b = PetState(updated_at=start)
        state_a.advance(start + 50, effort=float("nan"))
        state_b.advance(start + 50, effort=None)
        self.assertEqual(encode_pet_state(state_a), encode_pet_state(state_b))

    def test_workload_during_sleep_does_not_drain_energy(self):
        start = bond_stamp()
        state = PetState(updated_at=start, energy=19, sleeping=True)
        state.advance(start + 1800, effort=1.0)
        self.assertGreater(state.energy, 19)


if __name__ == "__main__":
    unittest.main()
