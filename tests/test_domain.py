
from aiko_pet.ui.view_models.care_text import format_care_response

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
import unittest
from datetime import datetime

from aiko_pet.pet.lifecycle import MAX_CATCHUP_SECONDS
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
        self.assertGreater(state.mood, 69)
        self.assertLess(state.mood, 75)
        self.assertAlmostEqual(state.fun, 72.4)
        self.assertAlmostEqual(state.energy, 69)

    def test_sleep_replenishes_energy(self):
        state = PetState(energy=30, sleeping=True, updated_at=NOW + 1000)
        state.advance(NOW + 1000 + 3 * 3600)
        self.assertEqual(state.energy, 96)
        self.assertAlmostEqual(state.satiety, 70.8)

    def test_offline_gap_is_capped(self):
        state = PetState(updated_at=NOW + 100)
        state.advance(NOW + 100 + MAX_CATCHUP_SECONDS * 9)
        self.assertLessEqual(state.satiety, 12)
        self.assertEqual(state.updated_at, NOW + 100 + MAX_CATCHUP_SECONDS * 9)

    def test_clock_going_backwards_does_not_penalize(self):
        state = PetState(updated_at=NOW + 5000)
        state.advance(NOW + 4500)
        self.assertEqual(state.satiety, 75)
        self.assertEqual(state.updated_at, NOW + 4500)

    def test_play_requires_an_actual_completed_game(self):
        state = PetState(satiety=99, mood=99, energy=10)
        before = encode_pet_state(state)
        self.assertIn("Spiel", format_care_response(state.interact("play")))
        self.assertEqual(encode_pet_state(state), before)
        self.assertIn("angenehm", format_care_response(state.interact("pet")))
        self.assertEqual(state.affection, 100)

    def test_play_when_exhausted_does_not_apply_cost(self):
        state = PetState(mood=20, energy=7)
        self.assertIn("müde", format_care_response(state.interact("play")))
        self.assertEqual((state.mood, state.energy), (20, 7))

    def test_sleep_toggle_and_feeding_wakes(self):
        state = PetState()
        state.interact("sleep")
        self.assertTrue(state.sleeping)
        state.interact("feed")
        self.assertFalse(state.sleeping)
        self.assertEqual(state.satiety, 100)

    def test_malformed_save_is_safely_normalized(self):
        state = decode_pet_state({
            "satiety": "NaN", "mood": -5, "energy": float("inf"),
            "sleeping": "yes", "updated_at": "oops",
        }, now=300)
        self.assertEqual((state.satiety, state.mood, state.energy), (75, 0, 75))
        self.assertFalse(state.sleeping)
        self.assertEqual(state.updated_at, 300)
        self.assertEqual(clamp_need_value(None), 75)

    def test_unknown_action_rejected(self):
        with self.assertRaises(ValueError):
            PetState().interact("delete")


if __name__ == "__main__":
    unittest.main()
