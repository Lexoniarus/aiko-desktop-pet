"""Distinct affection need, meaningful trust rewards and backwards-compatible saves."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.frontend.view_models.text_de import status_hint_text
from aiko_pet.infrastructure.pet_codec import decode_pet_state
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.state import PetState
from aiko_pet.pet.status_hints import StatusHint


def stamp(day: str = "2026-10-12", hour: int = 12) -> float:
    return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone().timestamp()


class AffectionNeedTests(unittest.TestCase):
    def test_completed_play_is_fun_and_company_not_affection(self):
        state = PetState(
            affection=17,
            mood=35,
            social=18,
            energy=50,
            satiety=50,
            fun=25,
        )
        state.record_game_experience(
            GameExperience(
                "rock_paper_scissors",
                3,
                successful_units=2,
                setback_units=1,
            ),
            now=stamp(),
        )
        self.assertGreater(state.fun, 25)
        self.assertGreater(state.social, 18)
        self.assertLess(state.energy, 50)
        self.assertEqual((state.affection, state.satiety), (17, 50))

    def test_food_and_energy_drinks_do_not_refill_affection(self):
        state = PetState(affection=16, satiety=23, energy=30)
        state.interact("feed", now=stamp())
        state.interact("energy_drink", now=stamp() + 1)
        self.assertEqual(state.affection, 16)
        self.assertEqual(state.energy, 40)

    def test_affection_decays_gently_even_under_heavy_work(self):
        start = stamp()
        idle = PetState(updated_at=start, affection=55, social=50)
        working = PetState(updated_at=start, affection=55, social=50)
        for minute in range(1, 121):
            point = start + minute * 60
            idle.advance(point, effort=0.0)
            working.advance(point, effort=1.0)
        self.assertAlmostEqual(idle.affection, working.affection)
        self.assertAlmostEqual(idle.affection, 55 - 2 * 6, places=2)
        self.assertLess(working.energy, idle.energy)
        self.assertLess(working.satiety, idle.satiety)

    def test_affection_slowly_declines_during_sleep_without_affecting_trust(self):
        start = datetime(2026, 10, 12, 23).timestamp()
        state = PetState(
            updated_at=start,
            affection=30,
            friendship=63,
            sleeping=True,
            sleep_origin="manual",
        )
        state.advance(start + 2 * 3600, effort=1.0)
        self.assertAlmostEqual(state.affection, 29.5, places=2)
        self.assertEqual(state.friendship, 63)

    def test_low_affection_has_gentle_mood_effect_distinct_from_social(self):
        start = stamp()
        comfortable = PetState(updated_at=start, affection=40, social=50)
        under_cared = PetState(updated_at=start, affection=15, social=50)
        comfortable.advance(start + 3600)
        under_cared.advance(start + 3600)
        self.assertLess(under_cared.mood, comfortable.mood)
        self.assertAlmostEqual(under_cared.social, comfortable.social)

    def test_affection_need_is_clamped_and_status_hint_is_distinct(self):
        state = decode_pet_state({"affection": "nan", "social": 80}, now=stamp())
        self.assertEqual(state.affection, 75)
        affection_hint = PetState(affection=5).status_hint()
        social_hint = PetState(social=5, affection=85).status_hint()
        self.assertIs(affection_hint, StatusHint.NEEDS_AFFECTION)
        self.assertIs(social_hint, StatusHint.LONELY)
        self.assertIn("Geste", status_hint_text(affection_hint))
        self.assertIn("Gesellschaft", status_hint_text(social_hint))
        self.assertEqual(decode_pet_state({"affection": -7}).affection, 0)
        self.assertEqual(decode_pet_state({"affection": 700}).affection, 100)


if __name__ == "__main__":
    unittest.main()
