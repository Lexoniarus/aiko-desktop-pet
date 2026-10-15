"""Needs, relationship rewards and observed workload regressions."""

from __future__ import annotations

from aiko_pet.pet.care_actions import plan_care_action

from aiko_pet.ui.view_models.care_text import format_care_response

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state

import json
import random
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.catalog import DialogueBook, Reaction
from aiko_pet.pet.lifecycle import MAX_LIVE_EFFORT_SECONDS
from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import context_at
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore


def require_reaction(value: Reaction | None) -> Reaction:
    """Fail immediately if an expected authored dialogue is unavailable."""
    assert value is not None, "Expected a dialogue reaction"
    return value


def timestamp(day: str = "2026-10-12", hour: int = 12) -> float:
    return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone().timestamp()


class NeedsAndBondTests(unittest.TestCase):
    def test_migration_from_old_save_keeps_existing_values(self):
        old = {"satiety": 28, "mood": 34, "energy": 41,
               "updated_at": timestamp(), "sleeping": False}
        state = decode_pet_state(old, now=timestamp())
        self.assertEqual((state.satiety, state.mood, state.energy), (28, 34, 41))
        self.assertEqual(state.social, 75)
        self.assertEqual(state.friendship, 15)
        self.assertEqual(state.friendship_level, 2)

    def test_corrupt_new_values_and_reward_history_are_bounded(self):
        state = decode_pet_state({
            "social": -20, "friendship": "nan", "updated_at": timestamp(),
            "care_last_rewards": {"feed": 9999999999,
                                  "pet": "malformed", "sleep": timestamp(),
                                  "unknown": 20},
        }, now=timestamp())
        self.assertEqual((state.social, state.friendship), (0, 15))
        self.assertEqual(state.care_last_rewards, {"sleep": timestamp()})

    def test_talk_is_distinct_from_play_and_food(self):
        state = PetState(social=12, satiety=28, mood=30, energy=60)
        state.interact("talk", now=timestamp())
        self.assertEqual(state.social, 38)
        self.assertGreater(state.mood, 30)
        self.assertEqual(state.satiety, 28)
        self.assertEqual(state.energy, 59)
        self.assertGreater(state.friendship, 15)

    def test_feeding_does_not_substitute_for_social_care(self):
        state = PetState(social=8, satiety=10)
        state.interact("feed", now=timestamp())
        self.assertEqual(state.social, 9)
        self.assertEqual(state.satiety, 40)
        state.interact("pet", now=timestamp() + 1)
        self.assertEqual(state.social, 11)
        self.assertEqual(state.affection, 100)
        before = encode_pet_state(state)
        state.interact("play", now=timestamp() + 2)
        self.assertEqual(encode_pet_state(state), before)

    def test_energy_drink_is_exactly_ten_points_and_can_be_stacked(self):
        state = PetState(energy=47, sleeping=True)
        start = timestamp()
        for n in range(5):
            state.interact("energy_drink", now=start + n)
        self.assertEqual(state.energy, 97)
        self.assertFalse(state.sleeping)
        state.interact("energy_drink", now=start + 7)
        self.assertEqual(state.energy, 100)
        before = encode_pet_state(state)
        self.assertIn("voll", format_care_response(state.interact("energy_drink", now=start + 8)))
        self.assertEqual(before, encode_pet_state(state))

    def test_night_energy_drink_prevents_immediate_auto_sleep(self):
        stamp = timestamp(hour=23) + 45 * 60
        state = PetState(updated_at=stamp, energy=18,
                         sleeping=True, sleep_origin="manual")
        state.interact("energy_drink", now=stamp)
        self.assertFalse(state.sleeping)
        state.advance(stamp + 1, auto_routine=True, allow_bedtime=True)
        self.assertFalse(state.sleeping)
        self.assertAlmostEqual(state.energy, 28, places=2)

    def test_manual_night_wake_also_honors_user_intervention(self):
        stamp = timestamp(hour=23) + 45 * 60
        state = PetState(updated_at=stamp, sleeping=True,
                         sleep_origin="manual")
        state.interact("sleep", now=stamp)
        state.advance(stamp + 1, auto_routine=True)
        self.assertFalse(state.sleeping)

    def test_energy_drink_never_increases_hunger_or_social(self):
        state = PetState(energy=0, satiety=41, mood=55, social=27)
        state.interact("energy_drink", now=timestamp())
        self.assertEqual((state.energy, state.satiety, state.social),
                         (10, 41, 27))

    def test_low_energy_play_is_rejected_without_bond_reward(self):
        state = PetState(energy=2)
        state.interact("play", now=timestamp())
        self.assertEqual((state.mood, state.social, state.friendship),
                         (75, 75, 15))

    def test_friendship_is_bond_not_spammable_status_bar(self):
        state = PetState()
        start = timestamp()
        state.interact("pet", now=start)
        first = state.friendship
        for i in range(100):
            state.interact("pet", now=start + i + 1)
        self.assertAlmostEqual(state.friendship, first)
        # Only another genuine need for care may earn trust after cooldown.
        state.affection = 55
        state.interact("pet", now=start + 13 * 60)
        self.assertGreater(state.friendship, first)

    def test_friendship_daily_cap_and_new_day(self):
        state = PetState(friendship=31)
        start = timestamp()
        for k in range(30):
            for action in ("feed", "pet", "talk", "play", "energy_drink"):
                state.energy = 65
                state.interact(action, now=start + 900 * k)
        self.assertLessEqual(state.friendship, 31 + 7.000001)
        previous = state.friendship
        state.social = 30
        state.interact("talk", now=start + 24 * 3600 + 1)
        self.assertGreater(state.friendship, previous)

    def test_friendship_does_not_decay_offline_or_during_busy_work(self):
        state = PetState(friendship=67, updated_at=timestamp())
        state.advance(timestamp() + 3600 * 24, effort=1.0)
        self.assertEqual(state.friendship, 67)
        self.assertLess(state.social, 75)

    def test_all_values_survive_real_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as dirname:
            store = StateStore(Path(dirname) / "state.json")
            start = timestamp()
            state = PetState(updated_at=start, social=14, friendship=63)
            state.interact("talk", now=start)
            store.save(state, PetSettings())
            session_data = store.load_session(now=start)
            loaded, _ = session_data.state, session_data.settings
            self.assertEqual(loaded.social, 40)
            self.assertAlmostEqual(loaded.friendship, state.friendship)
            self.assertEqual(loaded.care_last_rewards, state.care_last_rewards)
            payload = json.loads(store.path.read_text(encoding="utf-8"))
            self.assertNotIn("cpu", payload)
            self.assertNotIn("gpu", payload)
            self.assertNotIn("ram", payload)

    def test_friendship_display_level_is_bounded(self):
        self.assertEqual(PetState(friendship=0).friendship_level, 1)
        self.assertEqual(PetState(friendship=99.9).friendship_level, 10)
        self.assertEqual(PetState(friendship=100).friendship_level, 10)


class TelemetryEffortTests(unittest.TestCase):
    def test_high_work_accelerates_all_three_affected_stats(self):
        start = timestamp()
        calm = PetState(updated_at=start)
        busy = PetState(updated_at=start)
        for step in range(1, 361):
            point = start + step * 10
            calm.advance(point, effort=0.05)
            busy.advance(point, effort=1.0)
        self.assertLess(busy.satiety, calm.satiety - 1.2)
        self.assertLess(busy.mood, calm.mood - 1.5)
        self.assertLess(busy.energy, calm.energy - 2.0)
        self.assertAlmostEqual(busy.friendship, calm.friendship)

    def test_observed_load_cannot_be_extrapolated_over_offline_hours(self):
        start = timestamp()
        base = PetState(updated_at=start)
        busy = PetState(updated_at=start)
        base.advance(start + 8 * 3600)
        busy.advance(start + 8 * 3600, effort=1.0)
        self.assertLess(base.satiety - busy.satiety, 0.1)
        self.assertLess(base.mood - busy.mood, 0.1)
        self.assertLess(base.energy - busy.energy, 0.1)
        self.assertEqual(MAX_LIVE_EFFORT_SECONDS, 30)

    def test_missing_and_invalid_telemetry_use_normal_decay(self):
        start = timestamp()
        state_a = PetState(updated_at=start)
        state_b = PetState(updated_at=start)
        state_a.advance(start + 50, effort=float('nan'))
        state_b.advance(start + 50, effort=None)
        self.assertEqual(encode_pet_state(state_a), encode_pet_state(state_b))

    def test_workload_during_sleep_does_not_drain_energy(self):
        start = timestamp()
        state = PetState(updated_at=start, energy=19, sleeping=True)
        state.advance(start + 1800, effort=1.0)
        self.assertGreater(state.energy, 19)

    def test_24_7_idle_and_busy_keep_work_and_sleep_separate(self):
        start = timestamp()
        idle = PetState(updated_at=start, friendship=40)
        working = PetState(updated_at=start, friendship=40)
        # Four actual observed hours, six-second samples; no fake system uptime.
        for n in range(1, 2401):
            point = start + n * 6
            idle.advance(point, effort=0.03)
            working.advance(point, effort=0.95)
            if n == 600:  # Compare hunger before both values reach their floor.
                self.assertLess(working.satiety, idle.satiety)
        self.assertLess(working.mood, idle.mood)
        self.assertLess(working.energy, idle.energy)
        self.assertEqual(working.friendship, 40)


class SocialDialogueTests(unittest.TestCase):
    def setUp(self):
        self.mind = make_aiko_mind(started_at=0.0, rng=random.Random(57))
        self.context = context_at(timestamp())

    def test_social_deficit_is_distinct_emotion_and_dialogue(self):
        state = PetState(social=15)
        self.assertEqual(self.mind.emotion(state, 50), "lonely")
        self.assertEqual(require_reaction(self.mind.spontaneous_event(
            state, self.context, 50)).event, "social_low")
        self.assertEqual(require_reaction(self.mind.spontaneous_event(
            state, self.context, 55)).event, "idle")
        self.assertEqual(require_reaction(self.mind.spontaneous_event(
            state, self.context, 55 + 20 * 60)).event, "social_low")
        self.assertEqual(require_reaction(self.mind.click(
            "left", state, self.context, 60)).event, "click_lonely")
        self.assertEqual(self.mind.care_event(
            plan_care_action(
                state, "talk", now=self.context.local.timestamp(),
            ).result,
            self.mind.observe_care(state, self.context, 62),
        ), "talk_lonely")

    def test_new_friendship_dialogues_are_conditioned(self):
        state = PetState(friendship=88, social=78, mood=74)
        self.assertEqual(require_reaction(self.mind.click(
            "left", state, self.context, 40)).event, "click_close")
        self.assertEqual(self.mind.care_event(
            plan_care_action(
                state, "pet", now=self.context.local.timestamp(),
            ).result,
            self.mind.observe_care(state, self.context, 100),
        ), "pet_close")
        self.assertEqual(self.mind.care_event(
            plan_care_action(
                state, "talk", now=self.context.local.timestamp(),
            ).result,
            self.mind.observe_care(state, self.context, 100),
        ), "talk_close")

    def test_energy_drink_has_grounded_line_even_when_full(self):
        state = PetState(energy=100)
        self.assertEqual(self.mind.care_event(
            plan_care_action(
                state, "energy_drink", now=self.context.local.timestamp(),
            ).result,
            self.mind.observe_care(state, self.context, 90),
        ), "energy_drink_full")
        state.energy = 70
        self.assertEqual(self.mind.care_event(
            plan_care_action(
                state, "energy_drink", now=self.context.local.timestamp(),
            ).result,
            self.mind.observe_care(state, self.context, 91),
        ), "energy_drink")

    def test_new_dialogues_reference_only_existing_sprites(self):
        book = DialogueBook.from_file()
        new = [line for line in book.lines if line.id.startswith("v011-")]
        self.assertGreaterEqual(len(new), 35)
        self.assertTrue(all(line.animation in {
            'idle', 'waiting', 'review', 'failed', 'waving', 'jumping'
        } for line in new))
        self.assertTrue(all("GPU" not in line.text and "CPU" not in line.text
                            for line in new))


if __name__ == '__main__':
    unittest.main()
