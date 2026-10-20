"""Headless wish opportunities, original deadlines and durable disclosure."""

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.application.active_time import (
    ActiveSessionClock,
    SessionInputs,
    advance_session_time,
)
from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.session_time import SessionTimeProgression
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    WishArea,
    WishContext,
    WishId,
    WishState,
    acknowledge_wish_expression,
    create_wish,
    expire_wishes,
    wish_to_express,
)
from aiko_pet.world.contracts import WorldSurface
from aiko_pet.world.state import WorldState

DEFINITIONS = WISH_CATALOG.definitions


def create(
    state=WishState(), elapsed=0, context=WishContext(), definitions=DEFINITIONS
):
    return create_wish(
        state,
        elapsed=elapsed,
        sleeping=False,
        context=context,
        definitions=definitions,
        rng=random.Random(7),
    )


def select(
    state,
    elapsed=0,
    *,
    sleeping=False,
    friendship_level=3,
    mood=50,
    context=WishContext(),
):
    return wish_to_express(
        state,
        elapsed=elapsed,
        definitions=DEFINITIONS,
        sleeping=sleeping,
        friendship_level=friendship_level,
        mood=mood,
        context=context,
    )


class WishLifecycleTests(unittest.TestCase):
    def test_closed_and_standby_expiry_share_time_with_or_without_world(self):
        wall = 1800000000.0
        for with_world in (False, True):
            with (
                self.subTest(world=with_world),
                tempfile.TemporaryDirectory() as folder,
            ):
                wishes = WishState(
                    2,
                    (
                        ActiveWish(
                            1,
                            WishId.FOOD,
                            "apple",
                            0,
                            14400,
                        ),
                    ),
                    ((WishArea.FOOD, 0),),
                )
                pet = PetState(updated_at=wall, lived_seconds=14000, wishes=wishes)
                world = WorldState(WorldSurface(800, 600), ()) if with_world else None
                progression = (
                    SessionTimeProgression(world, ObjectMemory())
                    if world is not None
                    else None
                )
                settings = PetSettings(auto_routine=False)
                store = StateStore(Path(folder) / "state.json")
                store.save(pet, settings, world=world.snapshot() if world else None)
                closed = PetSessionRestorer(
                    store, wall_time=lambda: wall + 400
                ).restore()
                uptime = [10.0]
                clock = ActiveSessionClock(lambda: uptime[0])
                uptime[0] += 400
                advance_session_time(
                    pet,
                    clock,
                    SessionInputs(
                        wall + 400,
                        0,
                        False,
                        None,
                        False,
                        False,
                        None,
                    ),
                    progression=progression,
                )
                self.assertEqual(pet.wishes, closed.state.wishes)
                self.assertEqual(pet.wishes.active, ())
                self.assertEqual(pet.wishes.next_instance_id, 2)
                self.assertEqual(pet.lived_seconds, 14400)
                self.assertEqual(closed.state.lived_seconds, 14400)
                store.save(closed.state, settings)
                again = PetSessionRestorer(
                    store, wall_time=lambda: wall + 400
                ).restore()
                self.assertEqual(again.state.wishes, pet.wishes)

    def test_first_evaluation_and_area_limits_are_not_need_rewards(self):
        state = create()
        self.assertEqual(len(state.active), 1)
        self.assertEqual(state.active[0].expires_at, 14400)
        self.assertEqual(create(state, 3599), state)
        state = create(state, 3600)
        state = create(state, 7200)
        self.assertEqual(len(state.active), 3)
        self.assertEqual(
            len({DEFINITIONS[w.definition_id].area for w in state.active}), 3
        )
        self.assertEqual(create(state, 10800), state)

    def test_removed_wish_preserves_global_and_area_cooldowns_and_identity(self):
        definitions = {WishId.FOOD: DEFINITIONS[WishId.FOOD]}
        state = create(definitions=definitions)
        state = replace(state, active=())
        self.assertEqual(create(state, 3600, definitions=definitions), state)
        later = create(state, 5400, definitions=definitions)
        self.assertEqual(later.active[0].instance_id, 2)
        self.assertEqual(later.active[0].created_at, 5400)

    def test_selection_respects_capability_and_food_variety(self):
        definitions = {WishId.FACT: DEFINITIONS[WishId.FACT]}
        self.assertFalse(create(definitions=definitions).active)
        self.assertTrue(
            create(
                context=WishContext(online_social=True), definitions=definitions
            ).active
        )
        food = replace(DEFINITIONS[WishId.FOOD], targets=("apple", "cookie"))
        state = create(
            context=WishContext(repetitive_food="apple"),
            definitions={WishId.FOOD: food},
        )
        self.assertEqual(state.active[0].target_id, "cookie")
        self.assertFalse(
            create(
                context=WishContext(crowded=True),
                definitions={WishId.PET: DEFINITIONS[WishId.PET]},
            ).active
        )

    def test_sleep_and_closed_time_expire_without_generation_or_negative_effects(self):
        wishes = create()
        pet = PetState(updated_at=1800000000, wishes=wishes)
        pet.advance(1800014400, elapsed_seconds=14400, observed=False)
        self.assertEqual(pet.wishes.active, ())
        self.assertEqual(pet.wishes.next_instance_id, 2)
        self.assertEqual(pet.wishes.last_created_by_area, wishes.last_created_by_area)
        self.assertFalse(pet.moodlets.active)  # Four hours are not prolonged neglect.
        sleeping = create_wish(
            wishes,
            elapsed=14400,
            sleeping=True,
            context=WishContext(),
            definitions=DEFINITIONS,
            rng=random.Random(7),
        )
        self.assertEqual(sleeping.active, ())
        self.assertEqual(sleeping.next_instance_id, 2)
        self.assertEqual(expire_wishes(wishes, elapsed=14399), wishes)

    def test_inner_wish_survives_disclosure_thresholds_and_temporary_restrictions(self):
        state = create(definitions={WishId.PET: DEFINITIONS[WishId.PET]})
        for result in (
            select(state, friendship_level=2),
            select(state, mood=49),
            select(state, sleeping=True),
            select(state, context=WishContext(petting_welcome=False)),
        ):
            self.assertIsNone(result)
        self.assertEqual(select(state), state.active[0])
        self.assertIsNone(state.active[0].expressed_at)
        self.assertEqual(state.active[0].expires_at, 14400)
        api = create(
            context=WishContext(online_social=True),
            definitions={WishId.FACT: DEFINITIONS[WishId.FACT]},
        )
        self.assertIsNone(select(api))
        self.assertIsNone(select(api, context=WishContext(online_social=True)))
        self.assertIsNotNone(
            select(
                api,
                context=WishContext(
                    online_social=True, prepared_social=frozenset({"fact"})
                ),
            )
        )

    def test_receipt_spacing_expiry_and_restart_do_not_replay_or_renew(self):
        state = WishState(
            4,
            (
                ActiveWish(1, WishId.FOOD, "apple", 0, 14400),
                ActiveWish(2, WishId.CHAT, "chat", 3600, 18000),
                ActiveWish(3, WishId.PET, "pet", 7200, 21600),
            ),
            ((WishArea.FOOD, 0), (WishArea.SOCIAL, 3600), (WishArea.AFFECTION, 7200)),
        )
        selected = select(state, 7200)
        assert selected is not None
        self.assertEqual(selected.instance_id, 1)
        state = acknowledge_wish_expression(state, 1, elapsed=7200)
        self.assertEqual(acknowledge_wish_expression(state, 1, elapsed=7201), state)
        self.assertEqual(acknowledge_wish_expression(state, 999, elapsed=7201), state)
        self.assertIsNone(select(state, 8999))
        selected = select(state, 9000)
        assert selected is not None
        self.assertEqual(selected.instance_id, 2)
        self.assertEqual(acknowledge_wish_expression(state, 2, elapsed=8999), state)
        self.assertEqual(acknowledge_wish_expression(state, 2, elapsed=18000), state)
        pet = PetState(lived_seconds=7200, wishes=state)
        loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
        self.assertEqual(loaded.wishes, state)
        self.assertIsNone(select(loaded.wishes, 7200))
        checkpoint = loaded.capture_checkpoint()
        loaded.note_wish_expression(2)  # Spacing still applies after load.
        self.assertEqual(loaded.capture_checkpoint(), checkpoint)

    def test_return_creates_one_wish_without_other_effects(self):
        pet = PetState(lived_seconds=72000)
        before = pet.capture_checkpoint()
        pet.evaluate_wishes(WishContext(), rng=random.Random(7))
        self.assertEqual(len(pet.wishes.active), 1)
        self.assertEqual(pet.wishes.active[0].created_at, 72000)
        self.assertEqual(
            replace(pet.capture_checkpoint(), wishes=before.wishes), before
        )
