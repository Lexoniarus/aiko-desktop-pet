"""Care effects stay authoritative across tuning, dialogue and presentation."""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import patch

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.contact import acknowledge_interaction_text
from aiko_pet.application.controller import CareController
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.care_actions import plan_care_action
from aiko_pet.pet.care_result import CareEffect
from aiko_pet.pet.food import FOOD_BALANCE, FOOD_CATALOG, FoodState
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState
from aiko_pet.ui.view_models.care_text import format_care_response

STAMP = datetime(2026, 10, 12, 16).astimezone().timestamp()


class CareResultTests(unittest.TestCase):
    def test_petting_feedback_follows_actual_stages_without_refusal_care(self):
        state = PetState(affection=100, friendship=50, updated_at=STAMP)
        mind = make_aiko_mind(started_at=0)
        controller = CareController(state, mind, AdaptiveRoutine(),
                                    clock=ActiveSessionClock(lambda: 0.0))
        with patch.object(mind, "record_accepted_care") as accepted:
            for effect, event in (
                (CareEffect.AFFECTION_ENOUGH, "pet_enough"),
                (CareEffect.AFFECTION_ENOUGH_FIRM, "pet_enough_firm"),
                (CareEffect.AFFECTION_REFUSED, "pet_refused"),
                (CareEffect.AFFECTION_BOUNDARY_IGNORED, "pet_boundary_ignored"),
            ):
                with self.subTest(event=event):
                    outcome = controller.execute(CareCommand("pet"), self.inputs())
                    self.assertEqual(outcome.result.effect, effect)
                    assert outcome.reaction is not None
                    self.assertEqual(outcome.reaction.event, event)
                    self.assertTrue(format_care_response(outcome.result))
                    if effect == CareEffect.AFFECTION_REFUSED:
                        acknowledge_interaction_text(state, outcome.reaction.event)
            self.assertEqual(accepted.call_count, 2)

    def controller(self, state: PetState) -> CareController:
        return CareController(
            state, make_aiko_mind(started_at=0), AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0.0),
        )

    def inputs(self) -> SessionInputs:
        return SessionInputs(STAMP, 100, False, None, False, False, None)

    def test_changed_hunger_threshold_controls_every_care_consumer(self) -> None:
        for threshold, satiety, consumed, event in (
            (90.0, 95.0, False, "feed_full"),
            (100.0, 97.0, True, "feed_snack"),
        ):
            with self.subTest(threshold=threshold):
                state = PetState(
                    satiety=satiety, updated_at=STAMP, meals_date="2026-10-12",
                )
                controller = self.controller(state)
                previous = encode_pet_state(state)
                with (
                    patch("aiko_pet.pet.food.FOOD_BALANCE", replace(
                        FOOD_BALANCE, too_full_to_eat_threshold=threshold,
                    )),
                    patch("aiko_pet.pet.state.plan_care_action",
                          wraps=plan_care_action) as decide,
                ):
                    outcome = controller.execute(CareCommand("feed"), self.inputs())
                self.assertEqual(decide.call_count, 1)
                self.assertEqual(outcome.food_consumed, consumed)
                self.assertEqual(
                    outcome.consumed_item_id, "onigiri" if consumed else None,
                )
                assert outcome.reaction is not None
                self.assertEqual(outcome.reaction.event, event)
                if consumed:
                    self.assertGreater(state.satiety, satiety)
                    self.assertEqual(state.food.last_food_id, "onigiri")
                else:
                    self.assertEqual(encode_pet_state(state), previous)
                    self.assertEqual(outcome.result.effect, CareEffect.FOOD_SATISFIED)

    def test_drink_effect_controls_consumption_without_changing_nutrition(self) -> None:
        for energy in (80.0, 100.0):
            state = PetState(energy=energy, updated_at=STAMP)
            outcome = self.controller(state).execute(
                CareCommand("energy_drink"), self.inputs(),
            )
            self.assertFalse(outcome.food_consumed)
            self.assertEqual(
                outcome.consumed_item_id, "energy_drink" if energy < 100 else None,
            )
            self.assertEqual(state.food, FoodState())
            self.assertEqual(state.energy, min(100.0, energy + 10.0))

    def test_repeat_food_effect_and_wording_use_the_selected_food(self) -> None:
        for food_id, profile in FOOD_CATALOG.items():
            with self.subTest(food=food_id):
                state = PetState(
                    satiety=30, updated_at=STAMP,
                    food=FoodState(recent_food_ids=(food_id, food_id)),
                )
                result = state.interact("feed", now=STAMP, food_id=food_id)
                self.assertEqual(result.effect, CareEffect.FOOD_REPEAT)
                self.assertEqual(result.consumed_item_id, food_id)
                self.assertIn(profile.display_name, format_care_response(result))

    def test_version_one_pet_payload_roundtrips_with_original_rounding(self) -> None:
        state = PetState(
            satiety=42.123456, updated_at=STAMP, friendship=18.987654,
            food=FoodState(remaining_digest_minutes=12.123456),
        )
        encoded = encode_pet_state(state)
        self.assertEqual(encoded["satiety"], 42.1235)
        self.assertEqual(encoded["friendship"], 18.9877)
        self.assertEqual(encoded["food"], {
            "remaining_digest_minutes": 12.1235,
            "awake_hours_since_last_food": 0.0,
            "awake_hours_since_main_meal": 0.0,
            "recent_food_ids": [],
        })
        decoded = decode_pet_state(encoded, now=STAMP + 86400)
        self.assertEqual(encode_pet_state(decoded), encoded)


if __name__ == "__main__":
    unittest.main()
