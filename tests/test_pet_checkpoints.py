"""Immutable PetValues, pure preparation and identity-preserving recovery."""

from __future__ import annotations

import unittest
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields

from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.state import PetState

STAMP = 1_800_000_000.0


class PetCheckpointTests(unittest.TestCase):
    def test_checkpoint_covers_every_pet_field_without_writable_histories(self) -> None:
        pet = PetState(
            satiety=52,
            friendship=21,
            meals_today=["breakfast"],
            care_types_today=["pet"],
            care_last_rewards={"pet": 123.0},
            updated_at=STAMP,
        )
        checkpoint = pet.capture_checkpoint()
        self.assertEqual(
            {field.name for field in fields(checkpoint)},
            {field.name for field in fields(PetState)},
        )
        self.assertEqual(checkpoint.meals_today, ("breakfast",))
        self.assertEqual(checkpoint.care_types_today, ("pet",))
        self.assertEqual(checkpoint.care_last_rewards, (("pet", 123.0),))
        with self.assertRaises(FrozenInstanceError):
            setattr(checkpoint, "friendship", 99)
        with self.assertRaises(AttributeError):
            getattr(checkpoint.meals_today, "append")("lunch")

        pet.meals_today.append("lunch")
        pet.care_types_today.append("talk")
        pet.care_last_rewards["pet"] = 456.0
        self.assertEqual(checkpoint.meals_today, ("breakfast",))
        self.assertEqual(checkpoint.care_types_today, ("pet",))
        self.assertEqual(checkpoint.care_last_rewards, (("pet", 123.0),))

    def test_restore_keeps_identity_and_independent_histories(self) -> None:
        pet = PetState(
            satiety=42,
            friendship_day="2026-10-12",
            meals_today=["lunch"],
            care_types_today=["feed"],
            care_last_rewards={"feed": 12.0},
            updated_at=STAMP,
        )
        checkpoint = pet.capture_checkpoint()
        expected = deepcopy(pet)
        pet_id = id(pet)
        pet.meals_today.append("dinner")
        pet.care_types_today.clear()
        pet.care_last_rewards.clear()
        pet.satiety = 99
        pet.restore_checkpoint(checkpoint)
        self.assertEqual(id(pet), pet_id)
        self.assertEqual(pet, expected)
        self.assertEqual(encode_pet_state(pet), encode_pet_state(expected))

        pet.meals_today.append("breakfast")
        pet.care_types_today.append("talk")
        pet.care_last_rewards["talk"] = 50
        pet.restore_checkpoint(checkpoint)
        self.assertEqual(pet, expected)
        self.assertEqual(checkpoint.meals_today, ("lunch",))

    def test_preparation_matches_canonical_consumption_for_both_origins(self) -> None:
        for origin in (ConsumptionOrigin.AUTONOMOUS, ConsumptionOrigin.HANDOVER):
            with self.subTest(origin=origin):
                pet = PetState(
                    satiety=50,
                    social=30,
                    care_types_today=["talk"],
                    care_last_rewards={"talk": STAMP - 800},
                    updated_at=STAMP - 100,
                )
                before = pet.capture_checkpoint()
                prepared = pet.prepare_item_consumption(
                    "onigiri", origin, now=STAMP,
                )
                self.assertIsNotNone(prepared)
                assert prepared is not None
                self.assertEqual(pet.capture_checkpoint(), before)

                expected = deepcopy(pet)
                effect = expected.consume_item("onigiri", origin, now=STAMP)
                self.assertEqual(prepared.result, effect)
                self.assertEqual(prepared.checkpoint, expected.capture_checkpoint())
                pet.restore_checkpoint(prepared.checkpoint)
                self.assertEqual(pet, expected)

    def test_rejected_preparation_does_not_touch_pet(self) -> None:
        for pet, item in (
            (PetState(sleeping=True, satiety=50), "onigiri"),
            (PetState(satiety=100), "onigiri"),
            (PetState(energy=100), "energy_drink"),
        ):
            with self.subTest(item=item, sleeping=pet.sleeping):
                before = pet.capture_checkpoint()
                self.assertIsNone(
                    pet.prepare_item_consumption(
                        item, ConsumptionOrigin.HANDOVER, now=STAMP,
                    )
                )
                self.assertEqual(pet.capture_checkpoint(), before)

    def test_live_anchor_does_not_advance_needs_or_change_checkpoint_history(
        self,
    ) -> None:
        pet = PetState(
            satiety=56, meals_today=["breakfast"], updated_at=STAMP - 300,
        )
        pet.anchor_live_session(STAMP)
        self.assertEqual(pet.updated_at, STAMP)
        self.assertEqual(pet.satiety, 56)
        self.assertEqual(pet.meals_today, ["breakfast"])


if __name__ == "__main__":
    unittest.main()
