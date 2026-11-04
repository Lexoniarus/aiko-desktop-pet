
import unittest
from datetime import datetime

from aiko_pet.infrastructure.pet_codec import decode_pet_state
from aiko_pet.pet.state import PetState
from aiko_pet.pet.value_rules import clamp_need_value

NOW = datetime(2026, 10, 13, 12).timestamp()


class PetStateTests(unittest.TestCase):
    def test_defaults_are_friendly(self):
        state = PetState(updated_at=1)
        self.assertEqual((state.satiety, state.mood, state.energy), (75, 75, 75))
        self.assertFalse(state.sleeping)

    def test_normal_decay(self):
        state = PetState(updated_at=NOW + 1000)
        state.advance(NOW + 1000 + 3600)
        self.assertAlmostEqual(state.satiety, 67)
        self.assertAlmostEqual(state.mood, 55.52)
        self.assertAlmostEqual(state.fun, 72)
        self.assertAlmostEqual(state.energy, 72)

    def test_sleep_replenishes_energy(self):
        night = datetime(2026, 10, 12, 23).timestamp()
        state = PetState(energy=30, sleeping=True, updated_at=night)
        state.advance(night + 3 * 3600)
        self.assertAlmostEqual(state.energy, 52.5)
        self.assertAlmostEqual(state.satiety, 70.8)

    def test_offline_gap_is_fully_consumed(self):
        state = PetState(updated_at=NOW + 100)
        duration = 72 * 3600
        state.advance(NOW + 100 + duration)
        self.assertEqual(state.satiety, 0)
        self.assertEqual(state.energy, 0)
        self.assertEqual(state.lived_seconds, duration)
        self.assertEqual(state.updated_at, NOW + 100 + duration)

    def test_clock_going_backwards_does_not_penalize(self):
        state = PetState(updated_at=NOW + 5000)
        state.advance(NOW + 4500)
        self.assertEqual(state.satiety, 75)
        self.assertEqual(state.updated_at, NOW + 4500)

    def test_sleep_toggle_and_feeding_wakes(self):
        state = PetState()
        state.interact("sleep")
        self.assertTrue(state.sleeping)
        state.interact("feed")
        self.assertFalse(state.sleeping)
        self.assertEqual(state.satiety, 100)

    def test_malformed_save_is_safely_normalized(self):
        state = decode_pet_state(
            {
                "satiety": "NaN",
                "mood": -5,
                "energy": float("inf"),
                "sleeping": "yes",
                "updated_at": "oops",
            },
            now=300,
        )
        self.assertEqual((state.satiety, state.mood, state.energy), (75, 0, 75))
        self.assertFalse(state.sleeping)
        self.assertEqual(state.updated_at, 300)
        self.assertEqual(clamp_need_value(None), 75)

if __name__ == "__main__":
    unittest.main()
