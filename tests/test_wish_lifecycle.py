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
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wish_selection import replenish_wishes
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishContext,
    WishId,
    WishState,
    acknowledge_wish_expression,
    dismiss_wish,
    fulfill_activity_wish,
    set_wish_pinned,
    wish_to_express,
)
from aiko_pet.world.contracts import WorldSurface
from aiko_pet.world.state import WorldState

DEFINITIONS = WISH_CATALOG.definitions
NEEDS = NeedLevels(50, 80, 100, 100, 50)


def create(
    state=WishState(), elapsed=0, context=WishContext(), definitions=DEFINITIONS,
    needs=NEEDS,
):
    return replenish_wishes(
        state,
        elapsed=elapsed,
        sleeping=False,
        needs=needs,
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
    def test_initial_stock_rotates_at_ten_minutes_with_one_shared_clock(self):
        state = create()
        self.assertEqual(len(state.active), 3)
        self.assertEqual(state.refresh_at, 600)
        self.assertTrue(all(w.expires_at == 600 for w in state.active))
        self.assertEqual(create(state, 599.99), state)
        later = create(state, 600)
        self.assertEqual([w.instance_id for w in later.active], [4, 5, 6])
        self.assertEqual(later.refresh_at, 1200)
        self.assertEqual(create(later, 600), later)

    def test_fulfillment_and_dismissal_wait_for_existing_refresh(self):
        state = create(definitions={WishId.FOOD: replace(
            DEFINITIONS[WishId.FOOD], targets=("apple",),
        )})
        first = state.active[0]
        state = fulfill_activity_wish(
            state, WishArea.FOOD, first.target_id, elapsed=100,
            definitions=DEFINITIONS,
        ).state
        self.assertEqual(state.refresh_at, 600)
        self.assertFalse(state.active)
        self.assertEqual(create(state, 599), state)
        later = create(state, 600)
        self.assertEqual(later.active[0].instance_id, 2)
        removed = dismiss_wish(later, 2, elapsed=700)
        self.assertEqual(removed.refresh_at, 1200)
        self.assertEqual(dismiss_wish(removed, 2, elapsed=701), removed)

    def test_pin_survives_sleep_and_return_without_renewing_identity(self):
        state = create()
        first = state.active[0]
        state = set_wish_pinned(state, first.instance_id, True, elapsed=10)
        pinned = state.active[0]
        self.assertEqual(replace(pinned, pinned=False), first)
        asleep = replenish_wishes(
            state, elapsed=72000, sleeping=True, needs=NEEDS,
            context=WishContext(), definitions=DEFINITIONS, rng=random.Random(7),
        )
        self.assertEqual(asleep.active, (pinned,))
        self.assertEqual(asleep.refresh_at, 600)
        self.assertEqual(asleep.next_instance_id, 4)
        returned = create(asleep, 72000)
        self.assertEqual(returned.active[0], pinned)
        self.assertEqual([w.instance_id for w in returned.active], [1, 4, 5])
        self.assertEqual(returned.refresh_at, 72600)

    def test_late_unpin_keeps_goal_until_next_shared_refresh_and_roundtrips(self):
        state = create()
        state = replace(state, active=tuple(replace(w, pinned=True)
                                             for w in state.active))
        returned = create(state, 72000)
        wish = returned.active[0]
        unpinned = set_wish_pinned(returned, wish.instance_id, False, elapsed=72010)
        self.assertFalse(unpinned.active[0].pinned)
        self.assertEqual(unpinned.active[0].expires_at, 72600)
        self.assertEqual(unpinned.active[0].goal_snapshot, wish.goal_snapshot)
        pet = PetState(lived_seconds=72010, wishes=unpinned)
        loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
        self.assertEqual(loaded.wishes, unpinned)
        self.assertEqual(create(loaded.wishes, 72599), unpinned)
        self.assertNotIn(wish.instance_id,
                         [w.instance_id for w in create(unpinned, 72600).active])

    def test_expired_unpinned_wish_cannot_be_revived_by_stale_pin(self):
        state = create()
        expired = set_wish_pinned(state, state.active[0].instance_id, True,
                                 elapsed=600)
        self.assertFalse(expired.active)
        self.assertEqual(expired.next_instance_id, 4)
        self.assertEqual(expired.refresh_at, 600)

    def test_return_before_due_retains_original_stock_and_progress(self):
        state = create()
        self.assertEqual(create(state, 300), state)
        pet = PetState(lived_seconds=300, wishes=state)
        loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
        self.assertEqual(create(loaded.wishes, 599), state)

    def test_legacy_game_goal_and_progress_survive_until_original_expiry(self):
        old = ActiveWish(1, WishId.PLAY_GAME, "blackjack", 0, 14400,
                         game=GameWishProgress(("round:1",), 1, 0, "session:1"))
        state = WishState(2, (old,), ((WishArea.GAMES, 0),))
        later = create(state, 100)
        self.assertEqual(later.active[0], old)
        self.assertEqual(create(later, 700).active[0], old)
        self.assertNotIn(old, create(later, 14400).active)

    def test_pin_dismiss_and_refresh_have_no_care_or_emotional_effect(self):
        pet = PetState(lived_seconds=100)
        before = pet.capture_checkpoint()
        pet.evaluate_wishes(WishContext(), rng=random.Random(7))
        first = pet.wishes.active[0].instance_id
        pet.set_wish_pinned(first, True)
        pet.set_wish_pinned(first, False)
        pet.dismiss_wish(first)
        self.assertEqual(
            replace(pet.capture_checkpoint(), wishes=before.wishes), before,
        )

    def test_unavailable_existing_goal_is_kept_before_refresh(self):
        for key, context in (
            (WishId.FACT, WishContext(online_social=False)),
            (WishId.PET, WishContext(petting_welcome=False, crowded=True)),
            (WishId.PLAY_GAME, WishContext(games_ready=False)),
        ):
            with self.subTest(key=key):
                state = create(context=WishContext(online_social=True),
                               definitions={key: DEFINITIONS[key]})
                self.assertEqual(create(state, 100, context=context), state)

    def test_disclosure_remains_separate_from_inner_wishes(self):
        state = create(definitions={WishId.PET: DEFINITIONS[WishId.PET]})
        for settings in ({"friendship_level": 2}, {"mood": 49},
                         {"sleeping": True},
                         {"context": WishContext(petting_welcome=False)}):
            with self.subTest(settings=settings):
                self.assertIsNone(select(state, **settings))
        self.assertEqual(select(state), state.active[0])
        spoken = acknowledge_wish_expression(state, 1, elapsed=0)
        self.assertEqual(acknowledge_wish_expression(spoken, 1, elapsed=1), spoken)
        rotated = create(spoken, 600)
        self.assertIsNone(select(rotated, 600))  # Speech cooldown is not a wish timer.
        self.assertEqual(rotated.last_expressed_at, 0)

    def test_closed_and_standby_expire_without_replaying_wishes(self):
        wall = 1800000000.0
        for with_world in (False, True):
            with (
                self.subTest(world=with_world),
                tempfile.TemporaryDirectory() as folder,
            ):
                wishes = create()
                wishes = set_wish_pinned(wishes, 1, True, elapsed=10)
                pet = PetState(updated_at=wall, lived_seconds=500, wishes=wishes,
                               satiety=50, affection=50)
                world = WorldState(WorldSurface(800, 600), ()) if with_world else None
                progression = (SessionTimeProgression(world, ObjectMemory())
                               if world is not None else None)
                settings = PetSettings(auto_routine=False)
                store = StateStore(Path(folder) / "state.json")
                store.save(pet, settings, world=world.snapshot() if world else None)
                closed = PetSessionRestorer(
                    store, wall_time=lambda: wall + 400,
                ).restore()
                uptime = [10.0]
                clock = ActiveSessionClock(lambda: uptime[0])
                uptime[0] += 400
                advance_session_time(
                    pet, clock, SessionInputs(wall + 400, 0, False, None,
                                              False, False, None),
                    progression=progression,
                )
                self.assertEqual(pet.wishes, closed.state.wishes)
                self.assertEqual([w.instance_id for w in pet.wishes.active], [1])
                self.assertEqual(pet.wishes.next_instance_id, 4)
                self.assertEqual(pet.wishes.refresh_at, 600)
                self.assertFalse(pet.moodlets.active)
                pet.evaluate_wishes(WishContext(), rng=random.Random(7))
                self.assertEqual(pet.wishes.next_instance_id, 6)
                self.assertEqual(pet.wishes.refresh_at, 1500)
