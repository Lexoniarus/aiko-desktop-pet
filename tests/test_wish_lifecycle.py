"""Headless wish opportunities, original deadlines and durable disclosure."""

import random
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from itertools import product
from pathlib import Path
from unittest.mock import patch

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
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    WishArea,
    WishContext,
    WishId,
    WishState,
    acknowledge_wish_expression,
    expire_wishes,
    fulfill_activity_wish,
    replenish_wishes,
    retire_irrelevant_wishes,
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
    def test_pin_and_dismiss_are_neutral_and_keep_one_aggregate_refill_pause(self):
        state = create()
        pet = PetState(lived_seconds=100, wishes=state, moodlets=MoodletState(
            0, 2, (MoodletEpisode(1, MoodletId.PRIDE, 1, 0, 0, 7200),),
        ))
        before = pet.capture_checkpoint()
        first, second = (w.instance_id for w in state.active[:2])
        pet.set_wish_pinned(first, True)
        pinned = pet.wishes.active[0]
        self.assertEqual(replace(pinned, pinned=False), state.active[0])
        self.assertEqual(replace(pet.capture_checkpoint(), wishes=state), before)
        checkpoint = pet.capture_checkpoint()
        pet.set_wish_pinned(first, True)
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        pet.dismiss_wish(first)
        self.assertNotIn(first, [w.instance_id for w in pet.wishes.active])
        self.assertEqual(pet.wishes.refill_not_before, 820)
        self.assertEqual(replace(pet.capture_checkpoint(), wishes=state), before)
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), lived_seconds=200))
        pet.dismiss_wish(second)
        self.assertEqual(pet.wishes.refill_not_before, 820)
        self.assertEqual(pet.wishes.next_instance_id, state.next_instance_id)
        checkpoint = pet.capture_checkpoint()
        pet.dismiss_wish(first)  # A stale right-click cannot affect a replacement.
        pet.set_wish_pinned(first, True)
        self.assertEqual(pet.capture_checkpoint(), checkpoint)

    def test_unpin_keeps_original_expiry_and_late_unpin_starts_a_current_vacancy(self):
        for elapsed in (100, 20000):
            with self.subTest(elapsed=elapsed):
                wish = ActiveWish(1, WishId.FOOD, "apple", 0, 14400, pinned=True)
                pet = PetState(lived_seconds=elapsed, wishes=WishState(
                    2, (wish,), ((WishArea.FOOD, 0),),
                ))
                pet.set_wish_pinned(1, False)
                if elapsed < 14400:
                    self.assertEqual(pet.wishes.active, (replace(wish, pinned=False),))
                    self.assertFalse(expire_wishes(pet.wishes, elapsed=14400).active)
                else:
                    self.assertFalse(pet.wishes.active)
                    self.assertEqual(pet.wishes.refill_not_before, elapsed + 720)
        pinned = ActiveWish(1, WishId.FOOD, "apple", 0, 14400, pinned=True)
        later = ActiveWish(2, WishId.CHAT, "chat", 3600, 18000)
        expired = expire_wishes(WishState(
            3, (pinned, later), ((WishArea.FOOD, 0), (WishArea.SOCIAL, 3600)),
        ), elapsed=20000)
        self.assertEqual(expired.active, (pinned,))
        self.assertEqual(expired.refill_not_before, 18720)

    def test_expired_unpinned_goal_cannot_be_revived_by_a_pin_receipt(self):
        wish = ActiveWish(1, WishId.FOOD, "apple", 0, 14400)
        pet = PetState(lived_seconds=14400, wishes=WishState(
            2, (wish,), ((WishArea.FOOD, 0),),
        ))
        pet.set_wish_pinned(1, True)
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.wishes.refill_not_before, 15120)

    def test_pinned_activity_stays_eligible_past_deadline_without_forcing_care(self):
        for key, target, area, action, need in (
            (WishId.FOOD, "apple", WishArea.FOOD, "feed", "satiety"),
            (WishId.PET, "pet", WishArea.AFFECTION, "pet", "affection"),
        ):
            with self.subTest(key=key):
                wish = ActiveWish(1, key, target, 0, 14400, pinned=True)
                pet = PetState(lived_seconds=20000, friendship=0,
                               satiety=100, affection=100, wishes=WishState(
                                   2, (wish,), ((area, 0),),
                               ))
                pet.evaluate_wishes(WishContext(), rng=random.Random(7))
                before = pet.capture_checkpoint()
                food = "apple" if key == WishId.FOOD else None
                pet.interact(action, now=1800000000, food_id=food)
                self.assertIn(wish, pet.wishes.active)
                self.assertEqual(getattr(pet, need), 100)
                pet.restore_checkpoint(replace(before, **{need: 10}))
                pet.interact(action, now=1800000000, food_id=food)
                self.assertNotIn(wish, pet.wishes.active)
                self.assertEqual(pet.wishes.refill_not_before, 20720)
                self.assertEqual(pet.moodlets.active[0].definition_id,
                                 DEFINITIONS[key].fulfillment_moodlet)

    def test_food_and_affection_creation_use_current_needs_and_willingness(self):
        definitions = {key: DEFINITIONS[key] for key in (WishId.FOOD, WishId.PET)}
        for value, count in ((0, 2), (70, 2), (70.01, 0), (90, 0), (100, 0)):
            with self.subTest(value=value):
                wishes = create(needs=replace(NEEDS, satiety=value, affection=value),
                                definitions=definitions)
                self.assertEqual(len(wishes.active), count)
        denied = create(context=WishContext(petting_welcome=False),
                        definitions=definitions)
        self.assertEqual([w.definition_id for w in denied.active], [WishId.FOOD])

    def test_full_fun_social_and_temporary_game_restriction_do_not_block_inner_goals(
        self,
    ):
        full = NeedLevels(100, 0, 100, 100, 100)
        wishes = create(needs=full, context=WishContext(games_ready=False))
        self.assertEqual({DEFINITIONS[w.definition_id].area for w in wishes.active},
                         {WishArea.GAMES, WishArea.SOCIAL})
        self.assertEqual(len(wishes.active), 2)
        self.assertEqual(create(wishes, 100, needs=full), wishes)

    def test_unavailable_goals_are_not_replaced_or_renewed_at_live_evaluation(self):
        for key, context in (
            (WishId.FACT, WishContext(online_social=False)),
            (WishId.PET, WishContext(petting_welcome=False, crowded=True)),
            (WishId.PLAY_GAME, WishContext(games_ready=False)),
        ):
            with self.subTest(key=key):
                original = create(context=WishContext(online_social=True),
                                  definitions={key: DEFINITIONS[key]})
                later = create(original, 1000, context=context)
                self.assertEqual(later.active[0], original.active[0])
                self.assertEqual(later.active[0].expires_at, 14400)

    def test_only_supplied_unpinned_food_affection_retire_with_one_refill_pause(self):
        wishes = WishState(4, (
            ActiveWish(1, WishId.FOOD, "apple", 0, 14400),
            ActiveWish(2, WishId.PET, "pet", 0, 14400),
            ActiveWish(3, WishId.PLAY_GAME, "blackjack", 0, 14400),
        ), ((WishArea.FOOD, 0), (WishArea.GAMES, 0), (WishArea.AFFECTION, 0)))
        unchanged = create(wishes, 100, needs=replace(NEEDS, satiety=89.99,
                                                     affection=89.99))
        self.assertEqual(unchanged, wishes)
        first = create(wishes, 100, needs=replace(NEEDS, satiety=90))
        self.assertEqual({w.instance_id for w in first.active}, {2, 3})
        self.assertEqual(first.refill_not_before, 820)
        later = create(first, 200, needs=replace(NEEDS, satiety=100, affection=90))
        self.assertEqual({w.instance_id for w in later.active}, {3})
        self.assertEqual(later.refill_not_before, 820)
        pinned = replace(wishes, active=tuple(replace(w, pinned=True)
                                              for w in wishes.active))
        self.assertEqual(retire_irrelevant_wishes(
            pinned, elapsed=100, needs=NeedLevels(100, 100, 100, 100, 100),
            definitions=DEFINITIONS,
        ), pinned)

    def test_live_relevance_cleanup_is_neutral_and_desired_care_completes_first(self):
        wishes = WishState(2, (ActiveWish(1, WishId.FOOD, "apple", 0, 14400),),
                           ((WishArea.FOOD, 0),))
        pet = PetState(satiety=90, lived_seconds=100, wishes=wishes)
        before = pet.capture_checkpoint()
        pet.evaluate_wishes(WishContext(), rng=random.Random(7))
        self.assertEqual(pet.wishes.active, ())
        self.assertEqual(pet.wishes.refill_not_before, 820)
        self.assertEqual(replace(pet.capture_checkpoint(), wishes=before.wishes),
                         before)
        pet = PetState(satiety=81, lived_seconds=100, wishes=wishes)
        result = pet.interact("feed", food_id="apple", now=1800000000)
        self.assertTrue(result.food_consumed)
        self.assertGreaterEqual(pet.satiety, 90)
        pet.evaluate_wishes(WishContext(), rng=random.Random(7))
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.FOOD_FULFILLED)

    def test_game_weights_apply_within_area_and_preserve_current_goal_meanings(self):
        definitions = {key: d for key, d in DEFINITIONS.items()
                       if d.area == WishArea.GAMES}
        rng = random.Random(4)
        counts = Counter()
        for ticket in range(100):
            with patch.object(rng, "random", return_value=(ticket + .5) / 100):
                state = replenish_wishes(
                    WishState(), elapsed=0, sleeping=False, needs=NEEDS,
                    context=WishContext(), definitions=definitions, rng=rng,
                )
            wish = state.active[0]
            counts[wish.definition_id] += 1
            self.assertEqual(wish.goal_snapshot, ActiveWish(
                1, wish.definition_id, wish.target_id, 0, 14400,
            ).goal_snapshot)
        self.assertEqual(counts, {WishId.PLAY_GAME: 60, WishId.WIN_ROUND: 10,
                                  WishId.AVOID_ROUND_LOSS: 15,
                                  WishId.WIN_OVERALL: 10,
                                  WishId.AVOID_OVERALL_LOSS: 5})

    def test_due_refill_without_eligible_candidates_does_not_restart_the_pause(self):
        definitions = {WishId.FOOD: DEFINITIONS[WishId.FOOD]}
        state = create(definitions=definitions)
        state = fulfill_activity_wish(
            state, WishArea.FOOD, state.active[0].target_id, elapsed=100,
            definitions=definitions,
        ).state
        waiting = create(state, 820, needs=replace(NEEDS, satiety=100),
                         definitions=definitions)
        self.assertEqual(waiting, state)
        refilled = create(waiting, 900, definitions=definitions)
        self.assertEqual(refilled.active[0].created_at, 900)
        self.assertIsNone(refilled.refill_not_before)

    def test_closed_and_standby_expiry_share_time_with_or_without_world(self):
        wall = 1800000000.0
        for with_world, pinned in product((False, True), repeat=2):
            with (
                self.subTest(world=with_world, pinned=pinned),
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
                            pinned=pinned,
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
                self.assertEqual(pet.wishes.active, wishes.active if pinned else ())
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
        self.assertEqual(len(state.active), 3)
        self.assertEqual(state.active[0].expires_at, 14400)
        self.assertEqual(create(state, 3599), state)
        self.assertEqual(len(state.active), 3)
        self.assertEqual(
            len({DEFINITIONS[w.definition_id].area for w in state.active}), 3
        )
        self.assertEqual(create(state, 10800), state)

    def test_refill_pause_starts_at_fulfillment_and_survives_reload(self):
        definitions = {WishId.FOOD: DEFINITIONS[WishId.FOOD]}
        state = create(definitions=definitions)
        state = fulfill_activity_wish(
            state, WishArea.FOOD, state.active[0].target_id, elapsed=1000,
            definitions=definitions,
        ).state
        self.assertEqual(state.refill_not_before, 1720)
        pet = PetState(lived_seconds=1000, wishes=state)
        loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
        self.assertEqual(loaded.wishes, state)
        self.assertEqual(create(loaded.wishes, 1719, definitions=definitions), state)
        later = create(loaded.wishes, 1720, definitions=definitions)
        self.assertEqual(later.active[0].instance_id, 2)
        self.assertEqual(later.active[0].created_at, 1720)
        self.assertIsNone(later.refill_not_before)

    def test_multiple_vacancies_share_one_pause_and_fresh_identities(self):
        state = create()
        for elapsed, wish in zip((100, 200, 300), state.active):
            state = fulfill_activity_wish(
                state, DEFINITIONS[wish.definition_id].area, wish.target_id,
                elapsed=elapsed, definitions=DEFINITIONS,
            ).state
        self.assertEqual(state.refill_not_before, 820)
        self.assertEqual(create(state, 819), state)
        refilled = create(state, 820)
        self.assertEqual(len(refilled.active), 3)
        self.assertEqual({w.instance_id for w in refilled.active}, {4, 5, 6})
        self.assertEqual(create(refilled, 820), refilled)

    def test_expiry_uses_original_deadline_and_return_fills_only_current_stock(self):
        state = create()
        expired = expire_wishes(state, elapsed=14400)
        self.assertEqual(expired.refill_not_before, 15120)
        self.assertEqual(create(expired, 15119), expired)
        returned = create(expired, 72000)
        self.assertEqual(len(returned.active), 3)
        self.assertTrue(all(w.created_at == 72000 for w in returned.active))
        self.assertEqual(returned.next_instance_id, 7)

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
        # The later completion slice activates this form; test its suitability
        # contract now without enabling unsupported handover completion in runtime.
        avoid = replace(DEFINITIONS[WishId.AVOID_FOOD], selection_weight=1)
        definitions = {avoid.id: avoid}
        self.assertFalse(create(definitions=definitions).active)
        varied = create(context=WishContext(repetitive_food="apple"),
                        definitions=definitions)
        self.assertEqual(varied.active[0].target_id, "apple")
        self.assertEqual(varied.active[0].goal_snapshot, avoid.goal)
        self.assertFalse(create(context=WishContext(repetitive_food="apple"),
                                needs=replace(NEEDS, satiety=71),
                                definitions=definitions).active)

    def test_sleep_and_closed_time_expire_without_generation_or_negative_effects(self):
        wishes = create()
        pet = PetState(updated_at=1800000000, wishes=wishes)
        pet.advance(1800014400, elapsed_seconds=14400, observed=False)
        self.assertEqual(pet.wishes.active, ())
        self.assertEqual(pet.wishes.next_instance_id, 4)
        self.assertEqual(pet.wishes.last_created_by_area, wishes.last_created_by_area)
        self.assertFalse(pet.moodlets.active)  # Four hours are not prolonged neglect.
        sleeping = replenish_wishes(
            wishes,
            elapsed=14400,
            sleeping=True,
            needs=NEEDS,
            context=WishContext(),
            definitions=DEFINITIONS,
            rng=random.Random(7),
        )
        self.assertEqual(sleeping.active, ())
        self.assertEqual(sleeping.next_instance_id, 4)
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

    def test_return_replenishes_three_current_wishes_without_other_effects(self):
        pet = PetState(lived_seconds=72000, satiety=50)
        before = pet.capture_checkpoint()
        pet.evaluate_wishes(WishContext(), rng=random.Random(7))
        self.assertEqual(len(pet.wishes.active), 3)
        self.assertEqual(pet.wishes.active[0].created_at, 72000)
        self.assertEqual(
            replace(pet.capture_checkpoint(), wishes=before.wishes), before
        )
