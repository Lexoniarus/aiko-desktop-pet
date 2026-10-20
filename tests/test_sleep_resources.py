"""Finite acquired stock, paired restoration, rollback and restart-safe breaks."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.active_time import (
    ActiveSessionClock,
    SessionInputs,
    advance_session_time,
)
from aiko_pet.application.object_consumption import ObjectConsumption
from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.session_time import SessionTimeProgression
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.infrastructure.world_catalog import build_consumable_definitions
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.sleep import SleepContext
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.world.contracts import ObjectFootprint, ObjectState, WorldSurface
from aiko_pet.world.state import WorldState

START = datetime(2026, 10, 12, 23).timestamp()


def inputs(wall, automatic=True):
    return SessionInputs(
        wall, 0, automatic, None, False, False, None, sleep_context=SleepContext()
    )


class SleepResourceTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(
            WorldSurface(1000, 600, 60),
            build_consumable_definitions(DEFAULT_CATALOG, load_item_catalog()),
        )
        self.memory = ObjectMemory()
        self.progression = SessionTimeProgression(self.world, self.memory)
        self.pet = PetState(satiety=18, energy=20, updated_at=START)
        self.pet.interact("sleep", now=START)

    def food(self, name="apple", *, known=True):
        item = self.world.place_resting(
            name, 100 + 30 * len(self.world.snapshot().objects), ObjectFootprint(8, 8)
        )
        if known:
            assert item.position is not None
            self.memory.restore_snapshot((
                *self.memory.snapshot(),
                ObjectKnowledge(
                    item.instance_id,
                    name,
                    "drink" if name == "energy_drink" else "food",
                    item.position.x,
                    0,
                    True,
                    0,
                    assessed=True,
                    instance_id=item.instance_id,
                ),
            ))
        return item

    def advance(self, seconds, *, live=False):
        self.progression.advance(
            self.pet,
            inputs(START + seconds),
            START + seconds - self.pet.updated_at,
            reconstruct=not live,
        )

    def test_actual_known_food_reaches_target_and_counts_awake_break(self):
        self.pet.restore_checkpoint(replace(
            self.pet.capture_checkpoint(), wishes=WishState(2, (
                ActiveWish(1, WishId.FOOD, "apple", 0, 14400),
            ), ((WishArea.FOOD, 0),)),
        ))
        for _ in range(4):
            self.food()
        before_contact = self.pet.friendship_history.last_contact
        self.advance(3600)
        consumed = [
            o for o in self.world.snapshot().objects if o.state == ObjectState.CONSUMED
        ]
        self.assertGreater(len(consumed), 1)
        self.assertLess(len(consumed), 4)
        self.assertGreater(self.pet.satiety, 39)
        self.assertTrue(self.pet.sleeping)
        self.assertEqual(self.pet.friendship_history.last_contact, before_contact)
        self.assertEqual(self.pet.friendship_history.rewards, ())
        self.assertFalse(self.pet.wishes.active)
        self.assertEqual(self.pet.moodlets.active[0].definition_id,
                         MoodletId.FOOD_FULFILLED)
        self.assertAlmostEqual(
            self.pet.social,
            75 - 0.35 * (1 - len(consumed) / 60) - 8 * len(consumed) / 60,
            delta=0.06,
        )
        self.assertAlmostEqual(
            self.pet.sleep_episode.slept_seconds, 3600 - 60 * len(consumed), delta=15
        )

    def test_manual_sleep_protection_defers_food(self):
        self.food("sandwich")
        self.advance(1799)
        self.assertEqual(self.world.snapshot().objects[0].state, ObjectState.RESTING)
        self.assertTrue(self.pet.sleeping)
        self.advance(1815)
        self.assertEqual(self.world.snapshot().objects[0].state, ObjectState.CONSUMED)

    def test_unknown_food_and_energy_drinks_stay_untouched(self):
        unknown = self.food("sandwich", known=False)
        drink = self.food("energy_drink")
        self.advance(8 * 3600)
        self.assertLess(self.pet.satiety, 18)
        self.assertEqual(self.world.get(unknown.instance_id).state, ObjectState.RESTING)
        self.assertEqual(self.world.get(drink.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(self.pet.food.last_food_id)

    def test_identified_but_not_yet_appraised_food_is_not_used_offline(self):
        item = self.food("sandwich")
        known = self.memory.get(item.instance_id)
        assert known is not None
        self.memory.restore_snapshot((replace(known, assessed=False),))
        self.advance(3600)
        self.assertEqual(self.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(self.pet.food.last_food_id)

    def test_moved_missing_held_and_wrong_identity_stock_is_not_accessible(self):
        item = self.food("sandwich")
        known = self.memory.get(item.instance_id)
        assert known is not None
        for change in (
            {"x": known.x + 10},
            {"place_status": "missing"},
            {"resting": False},
            {"identity": "apple"},
        ):
            self.memory.restore_snapshot((replace(known, **change),))
            self.assertEqual(
                ObjectConsumption.remembered_stock(self.world, self.memory), ()
            )
        self.memory.restore_snapshot((known,))
        self.world.take_resting(item.instance_id, expected_revision=0)
        self.assertEqual(
            ObjectConsumption.remembered_stock(self.world, self.memory), ()
        )

    def test_wrong_remembered_place_triggers_only_one_food_check(self):
        item = self.food("sandwich")
        self.world.move_resting(item.instance_id, 500, expected_revision=0)
        self.advance(1800)
        self.assertTrue(self.pet.sleep_episode.care_break)
        self.assertEqual(self.world.get(item.instance_id).state, ObjectState.RESTING)
        self.advance(2100)
        self.assertTrue(self.pet.sleep_episode.food_failed)
        slept = self.pet.sleep_episode.slept_seconds
        self.advance(2700)
        self.assertAlmostEqual(self.pet.sleep_episode.slept_seconds - slept, 600)
        self.assertEqual(self.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertIsNone(self.pet.food.last_food_id)

        current = self.world.get(item.instance_id)
        self.world.move_resting(
            item.instance_id, 100, expected_revision=current.revision,
        )
        self.advance(2701, live=True)
        self.assertTrue(self.pet.sleep_episode.care_break)

    def test_stock_exhaustion_does_not_invent_more_portions(self):
        self.food()
        self.advance(8 * 3600)
        self.assertEqual(
            sum(o.state == ObjectState.CONSUMED for o in self.world.snapshot().objects),
            1,
        )
        self.assertTrue(self.pet.sleep_episode.food_failed or not self.pet.sleeping)
        self.assertLess(self.pet.satiety, 40)

    def test_failed_live_search_is_bounded_and_survives_restart(self):
        self.pet = PetState(satiety=0, energy=20, updated_at=START)
        self.pet.interact("sleep", now=START)
        self.advance(1800, live=True)
        self.assertTrue(self.pet.sleep_episode.care_break)
        for seconds in range(1815, 2116, 15):
            self.advance(seconds, live=True)
        self.assertTrue(self.pet.sleep_episode.food_failed)
        self.assertTrue(self.pet.sleeping)
        from aiko_pet.infrastructure.pet_codec import decode_pet_state

        self.pet = decode_pet_state(encode_pet_state(self.pet))
        self.advance(2400, live=True)
        self.assertFalse(self.pet.sleep_episode.care_break)
        self.food("sandwich")
        self.advance(2415, live=True)
        self.assertTrue(self.pet.sleep_episode.care_break)

    def test_expired_break_waits_for_safe_release_of_an_unconsumed_held_portion(self):
        item = self.food()
        self.advance(1800, live=True)
        self.world.collect_resting(item.instance_id, expected_revision=0)
        self.advance(2400, live=True)
        self.assertFalse(self.pet.sleeping)
        self.assertTrue(self.pet.sleep_episode.care_break)
        held = self.world.get(item.instance_id)
        self.world.put_down(item.instance_id, 100, expected_revision=held.revision)
        self.advance(2401, live=True)
        self.assertTrue(self.pet.sleeping)
        self.assertTrue(self.pet.sleep_episode.food_failed)

    def test_saved_search_expires_in_closed_time(self):
        self.pet = PetState(satiety=0, energy=20, updated_at=START)
        self.pet.interact("sleep", now=START)
        self.advance(1800, live=True)
        self.assertTrue(self.pet.sleep_episode.care_break)
        self.advance(2400)
        self.assertTrue(self.pet.sleeping)
        self.assertTrue(self.pet.sleep_episode.food_failed)

    def test_pair_and_clock_roll_back_if_memory_commit_fails(self):
        self.food("sandwich")
        before = (
            self.pet.capture_checkpoint(),
            self.world.snapshot(),
            self.memory.snapshot(),
        )
        uptime = [0.0]
        clock = ActiveSessionClock(lambda: uptime[0])
        uptime[0] = 3600
        with patch.object(
            self.memory, "record_consumption", side_effect=RuntimeError("failed")
        ):
            with self.assertRaises(RuntimeError):
                advance_session_time(
                    self.pet, clock, inputs(START + 3600), progression=self.progression,
                )
        self.assertEqual(
            (
                self.pet.capture_checkpoint(),
                self.world.snapshot(),
                self.memory.snapshot(),
            ),
            before,
        )
        advance_session_time(
            self.pet, clock, inputs(START + 3600), progression=self.progression,
        )
        self.assertEqual(self.pet.lived_seconds, 3600)
        self.assertEqual(self.world.snapshot().objects[0].state, ObjectState.CONSUMED)

    def test_batch_steps_and_standby_agree_on_finite_stock(self):
        self.food("sandwich")
        initial = (self.pet.capture_checkpoint(), self.world.snapshot(),
                   self.memory.snapshot())
        self.advance(3600)
        expected = (self.pet.capture_checkpoint(), self.world.snapshot(),
                    self.memory.snapshot())
        for mode in ("steps", "standby"):
            with self.subTest(mode=mode):
                self.pet.restore_checkpoint(initial[0])
                self.world.restore_snapshot(initial[1])
                self.memory.restore_snapshot(initial[2])
                if mode == "steps":
                    for seconds in range(15, 3601, 15):
                        self.advance(seconds)
                else:
                    uptime = [100.0]
                    clock = ActiveSessionClock(lambda: uptime[0])
                    uptime[0] += 3600
                    advance_session_time(
                        self.pet, clock, inputs(START + 3600),
                        progression=self.progression,
                    )
                self.assertEqual(self.world.snapshot(), expected[1])
                self.assertEqual(self.memory.snapshot(), expected[2])
                for name in ("satiety", "energy", "social", "affection",
                             "mood", "friendship"):
                    self.assertAlmostEqual(
                        getattr(self.pet, name), getattr(expected[0], name), delta=.01,
                    )

    def test_awake_hunger_without_food_does_not_block_known_drink(self):
        self.pet = PetState(satiety=0, energy=40, updated_at=START + 13 * 3600)
        drink = self.food("energy_drink")
        before = self.pet.friendship_history.last_contact
        self.progression.advance(
            self.pet, inputs(START + 13 * 3600 + 60, automatic=False), 60,
            reconstruct=True,
        )
        self.assertEqual(self.world.get(drink.instance_id).state, ObjectState.CONSUMED)
        self.assertGreater(self.pet.energy, 40)
        self.assertEqual(self.pet.friendship_history.last_contact, before)
        self.assertEqual(self.pet.friendship_history.rewards, ())

    def test_legacy_relationship_migration_is_neutral_across_resource_steps(self):
        self.food("sandwich")
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            store.save(
                self.pet,
                PetSettings(),
                world=self.world.snapshot(),
                object_memory=self.memory.export(now=0),
            )
            raw = json.loads(store.path.read_text(encoding="utf-8"))
            raw["pet"].pop("relationship")
            store.path.write_text(json.dumps(raw), encoding="utf-8")
            first = PetSessionRestorer(
                store, wall_time=lambda: START + 12 * 3600
            ).restore()
            self.assertEqual(first.state.friendship, self.pet.friendship)
            self.assertEqual(first.state.friendship_history.baseline, 12 * 3600)
            self.assertIsNone(first.state.friendship_history.last_contact)

    def test_paired_store_restores_stock_before_catchup_and_reopen_is_exactly_once(
        self,
    ):
        self.food("sandwich")
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            store.save(
                self.pet,
                PetSettings(),
                adaptive=AdaptiveMemory(),
                world=self.world.snapshot(),
                object_memory=self.memory.export(now=0),
            )
            first = PetSessionRestorer(store, wall_time=lambda: START + 3600).restore()
            assert first.world is not None
            self.assertGreater(first.state.satiety, 40)
            self.assertFalse(first.world.objects[0].state == ObjectState.RESTING)
            store.save(
                first.state,
                first.settings,
                adaptive=first.adaptive.memory,
                world=first.world,
                object_memory=first.object_memory,
            )
            second = PetSessionRestorer(store, wall_time=lambda: START + 3600).restore()
            self.assertEqual(
                encode_pet_state(second.state), encode_pet_state(first.state)
            )
            assert second.world is not None
            self.assertEqual(second.world.objects, ())

    def test_bad_future_episode_and_quiet_window_are_backed_up_without_resetting_needs(
        self,
    ):
        for section in ("sleep_episode", "quiet_window"):
            with self.subTest(section=section), tempfile.TemporaryDirectory() as folder:
                store = StateStore(Path(folder) / "state.json")
                store.save(self.pet, PetSettings(), adaptive=AdaptiveMemory())
                raw = json.loads(store.path.read_text(encoding="utf-8"))
                raw["pet" if section == "sleep_episode" else "adaptive"][section] = {
                    "version": 999
                }
                original = json.dumps(raw).encode("utf-8")
                store.path.write_bytes(original)
                loaded = store.load_session(now=START)
                self.assertEqual(loaded.state.satiety, self.pet.satiety)
                store.save(
                    loaded.state, loaded.settings, adaptive=loaded.adaptive_memory
                )
                backups = list(Path(folder).glob("*.aiko-save-backup"))
                self.assertEqual(backups[0].read_bytes(), original)

    def test_prolonged_hunger_uses_only_actual_known_stock(self):
        self.food()
        self.advance(3 * 3600)
        self.assertNotIn(MoodletId.HUNGER_WORN,
                         [e.definition_id for e in self.pet.moodlets.active])
        self.assertEqual(sum(o.state == ObjectState.CONSUMED
                             for o in self.world.snapshot().objects), 1)
        self.setUp()
        unknown = self.food(known=False)
        self.advance(3 * 3600)
        hunger = next(e for e in self.pet.moodlets.active
                      if e.definition_id == MoodletId.HUNGER_WORN)
        self.assertEqual(hunger.level, 1)
        self.assertEqual(self.world.get(unknown.instance_id).state, ObjectState.RESTING)
