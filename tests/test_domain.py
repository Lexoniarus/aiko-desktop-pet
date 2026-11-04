
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
