"""Wish storage retains original flexible goals and pending personal transfers."""

import copy
import unittest
from dataclasses import replace

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.infrastructure.wish_codec import decode_wishes, encode_wishes
from aiko_pet.pet.food_handover import (
    MAX_FOOD_HANDOVERS,
    FoodHandoverReceipt,
    FoodWishSnapshot,
    HandoverStatus,
)
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishId,
    WishState,
)


def state():
    wishes = []
    for instance, key, reference in (
        (1, WishId.PLAY_GAME, "mastermind"),
        (2, WishId.PLAY_ANY_GAME, None),
        (3, WishId.PLAY_OTHER_GAME, "mastermind"),
    ):
        definition = WISH_CATALOG.definitions[key]
        at = instance * 100
        wishes.append(
            ActiveWish(
                instance,
                key,
                reference or "",
                at,
                at + 14400,
                game=GameWishProgress(("a:1",), 0, 1)
                if instance == 1
                else GameWishProgress(),
                goal=definition.goal,
                pinned=instance == 1,
                target=definition.bind_target(reference),
            )
        )
    food = WISH_CATALOG.definitions[WishId.AVOID_FOOD]
    context = FoodWishSnapshot(
        4, food.id, food.bind_target("donut"), food.goal, 50, 200, True
    )
    return WishState(
        8,
        tuple(wishes),
        ((WishArea.FOOD, 50), (WishArea.GAMES, 300)),
        refresh_at=1200,
        food_handovers=(
            FoodHandoverReceipt(
                "offer:1",
                "item:9",
                500,
                (context,),
            ),
        ),
    )


class WishStateStorageTests(unittest.TestCase):
    def test_multiple_game_goals_and_retired_food_context_round_trip_as_one_pet(self):
        original = state()
        self.assertEqual(decode_wishes(encode_wishes(original), 1000), original)
        pet = PetState(updated_at=1800000000, lived_seconds=1000, wishes=original)
        before = pet.capture_checkpoint()
        loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
        self.assertEqual(loaded.capture_checkpoint(), before)
        loaded.restore_checkpoint(replace(before, wishes=WishState()))
        loaded.restore_checkpoint(before)
        self.assertEqual(loaded.wishes, original)
        self.assertEqual(copy.deepcopy(pet).capture_checkpoint(), before)
        # Unknown identity and the retired original wish survive independently.
        self.assertIsNone(loaded.wishes.food_handovers[0].recognized_food_id)
        self.assertNotIn(4, {w.instance_id for w in loaded.wishes.active})
        self.assertEqual(loaded.wishes.active[0].game.completed_rounds, 1)

    def test_old_save_does_not_invent_refresh_schedule_or_handover_evidence(self):
        definition = WISH_CATALOG.definitions[WishId.PLAY_GAME]
        old = WishState(
            2,
            (ActiveWish(1, definition.id, "blackjack", 10, 14410),),
            ((WishArea.GAMES, 10),),
        )
        raw = encode_wishes(old)
        for field in ("refresh_at", "food_handovers"):
            del raw[field]
        del raw["active"][0]["target"]
        restored = decode_wishes(raw, 1000)
        self.assertEqual(restored, old)
        self.assertIsNone(restored.refresh_at)
        self.assertFalse(restored.food_handovers)
        raw["refill_not_before"] = 1720
        migrated = decode_wishes(raw, 1000)
        self.assertEqual(migrated.refresh_at, 1720)
        rewritten = encode_wishes(migrated)
        self.assertNotIn("refill_not_before", rewritten)
        self.assertEqual(decode_wishes(rewritten, 1000), migrated)
        raw["refresh_at"] = 1700
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            decode_wishes(raw, 1000)

    def test_malformed_targets_schedules_and_duplicate_goals_are_rejected(self):
        original = encode_wishes(state())
        for mutate in (
            lambda r: r.update(refresh_at=1721),
            lambda r: r.update(refresh_at=True),
            lambda r: r["active"][1].update(target_id="blackjack"),
            lambda r: r["active"][1]["target"].update(mode="exact"),
            lambda r: r["active"][2]["target"].update(target_id="missing"),
            lambda r: r["active"][1].update(instance_id=1),
            lambda r: r["active"].__setitem__(1, {**r["active"][0], "instance_id": 2}),
        ):
            raw = copy.deepcopy(original)
            mutate(raw)
            with self.assertRaises(ValueError):
                decode_wishes(raw, 1000)

    def test_transfer_recognition_accounting_and_cancellation_remain_distinct(self):
        original = state()
        pending = original.food_handovers[0]
        for receipt in (
            pending,
            replace(pending, status=HandoverStatus.CANCELLED),
            replace(
                pending,
                recognized_food_id="apple",
                recognized_at=900,
                status=HandoverStatus.EVALUATED,
                resolved_wish_instance_id=4,
                accounted_wish_ids=(4,),
            ),
        ):
            stored = replace(original, food_handovers=(receipt,))
            self.assertEqual(decode_wishes(encode_wishes(stored), 1000), stored)
        raw = encode_wishes(original)
        for field, bad in (
            ("recognized_food_id", "donut"),
            ("recognized_at", 499),
            ("status", "evaluated"),
            ("resolved_wish_instance_id", 4),
            ("accounted_wish_ids", [5]),
            ("accounted_wish_ids", [4, 4]),
        ):
            altered = copy.deepcopy(raw)
            altered["food_handovers"][0][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_wishes(altered, 1000)
        for receipts in (
            raw["food_handovers"] * (MAX_FOOD_HANDOVERS + 1),
            [
                raw["food_handovers"][0],
                {**raw["food_handovers"][0], "handover_id": "new"},
            ],
        ):
            with self.assertRaises(ValueError):
                decode_wishes({**raw, "food_handovers": receipts}, 1000)
