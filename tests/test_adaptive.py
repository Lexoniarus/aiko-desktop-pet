"""Regression and long-running deterministic simulations of Aiko's rhythm."""

import ctypes
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from aiko_pet.desktop.global_input import idle_seconds_windows
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.adaptive_models import SLOTS, AdaptiveMemory, Observation
from aiko_pet.pet.mind.dialogue_context import SituationalCondition
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.sleep import SleepContext
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session


def local_stamp(day, hour, minute=0):
    return (
        datetime
        .fromisoformat(f"{day}T{hour:02d}:{minute:02d}:00")
        .astimezone()
        .timestamp()
    )


class AdaptiveBehaviourTests(unittest.TestCase):
    def test_no_phantom_72_hour_work_from_system_uptime(self):
        engine = AdaptiveRoutine()
        state = PetState(energy=45, updated_at=local_stamp("2026-10-12", 7))
        start = state.updated_at
        observed_night_sleep = False
        for tick in range(72 * 120):
            stamp = start + tick * 30
            hour = context_at(stamp).local.hour
            hard = 10 <= hour < 14
            engine.observe(
                Observation(
                    stamp,
                    0.90 if hard else 0.05,
                    0 if hard else 4000,
                    uptime_hours=tick / 120,
                ),
                tick * 30.0,
                energy=state.energy,
                sleeping=state.sleeping,
            )
            state.advance(
                stamp,
                auto_routine=True,
                sleep_context=engine.observe_input(
                    wall=stamp, monotonic=tick * 30.0, idle_seconds=0 if hard else 4000
                ),
            )
            if context_at(stamp).night and state.sleeping:
                observed_night_sleep = True
        self.assertTrue(observed_night_sleep)
        self.assertGreater(state.energy, 40)
        final_situation = engine.current
        assert final_situation is not None
        self.assertLess(final_situation.strain, 70)
        self.assertGreater(engine.memory.hour_seconds[10], 0)
        self.assertLess(engine.memory.strain, 70)

    def test_background_computation_does_not_prevent_night_sleep(self):
        start = local_stamp("2026-10-12", 23, 40)
        for effort in (0.04, 0.98):
            engine = AdaptiveRoutine()
            state = PetState(updated_at=start, energy=65)
            for tick in range(140):
                stamp = start + tick * 30
                engine.observe(
                    Observation(stamp, effort, 5000),
                    tick * 30.0,
                    energy=state.energy,
                    sleeping=state.sleeping,
                )
                state.advance(
                    stamp,
                    auto_routine=True,
                    sleep_context=engine.observe_input(
                        wall=stamp, monotonic=tick * 30.0, idle_seconds=5000
                    ),
                )
            self.assertTrue(state.sleeping)
            self.assertEqual(state.sleep_episode.kind, "main")

    def test_manual_sleep_is_not_overridden_by_work(self):
        now = local_stamp("2026-10-12", 23, 50)
        pet = PetState(updated_at=now, sleeping=True, sleep_origin="manual")
        pet.advance(now + 100, auto_routine=True, allow_bedtime=False)
        self.assertTrue(pet.sleeping)
        self.assertEqual(pet.sleep_episode.kind, "main")

    def test_night_activity_alone_is_not_forced_bedtime(self):
        now = local_stamp("2026-10-13", 1)
        state = PetState(updated_at=now, energy=12)
        state.advance(
            now,
            auto_routine=True,
            sleep_context=SleepContext(idle_seconds=0, observed=True),
        )
        self.assertFalse(state.sleeping)

    def test_daytime_nap_ends_and_cannot_repeat_indefinitely(self):
        start = local_stamp("2026-10-12", 14)
        state = PetState(updated_at=start, energy=20)
        engine = AdaptiveRoutine()
        begun, finished = False, False
        for tick in range(160):
            stamp = start + tick * 30
            engine.observe(
                Observation(stamp, 0.04, 5000, 72),
                tick * 30.0,
                energy=state.energy,
                sleeping=state.sleeping,
            )
            state.advance(
                stamp,
                auto_routine=True,
                sleep_context=engine.observe_input(
                    wall=stamp, monotonic=tick * 30.0, idle_seconds=5000
                ),
            )
            if state.sleep_origin == "nap":
                begun = True
            if begun and not state.sleeping:
                finished = True
        self.assertTrue(begun)
        self.assertTrue(finished)
        self.assertFalse(state.sleeping)
        self.assertEqual(state.auto_nap_day, "2026-10-12")
        self.assertGreater(state.energy, 8)

    def test_missing_telemetry_does_not_fabricate_work(self):
        start = local_stamp("2026-10-12", 13)
        engine = AdaptiveRoutine()
        engine.observe(
            Observation(start, None, None, 100), 0, energy=70, sleeping=False
        )
        view = engine.observe(
            Observation(start + 30, None, None, 100), 30, energy=70, sleeping=False
        )
        self.assertIsNone(view.effort)
        self.assertEqual(sum(engine.memory.hour_seconds), 0)
        self.assertEqual(view.strain, 0)

    def test_brief_peak_has_less_cost_than_an_hour_of_work(self):
        start = local_stamp("2026-10-12", 16)
        burst = AdaptiveRoutine()
        burst.observe(Observation(start, 0.97, 0), 0, energy=70, sleeping=False)
        result = burst.observe(
            Observation(start + 6, 0.03, 0), 6, energy=70, sleeping=False
        )
        long_job = AdaptiveRoutine()
        for tick in range(121):
            long_job.observe(
                Observation(start + tick * 30, 0.97, 0),
                tick * 30,
                energy=70,
                sleeping=False,
            )
        self.assertLess(result.strain, 1)
        sustained_situation = long_job.current
        assert sustained_situation is not None
        self.assertGreater(sustained_situation.strain, result.strain + 20)

    def test_one_abnormal_day_does_not_change_the_long_term_profile(self):
        start = local_stamp("2026-10-12", 20)
        engine = AdaptiveRoutine()
        for tick in range(100):
            engine.observe(
                Observation(start + tick * 30, 0.99, 0),
                tick * 30,
                energy=80,
                sleeping=False,
            )
        final_situation = engine.current
        assert final_situation is not None
        self.assertFalse(final_situation.expectation_confident)
        self.assertIsNone(final_situation.expected_effort)

    def test_profile_learns_repeated_weekday_hour_slowly(self):
        start = local_stamp("2026-10-12", 20)
        engine = AdaptiveRoutine()
        clock = 0
        for week in range(5):
            # Keep the same local weekday/hour across the October DST boundary.
            target = (datetime.fromtimestamp(start) + timedelta(weeks=week)).timestamp()
            # No hidden extrapolation during one week's gap.
            engine.observe(
                Observation(target, 0.88, 0), clock, energy=80, sleeping=False
            )
            clock += 30
            for sample in range(1, 15):
                reading = engine.observe(
                    Observation(target + sample * 30, 0.88, 0),
                    clock,
                    energy=80,
                    sleeping=False,
                )
                clock += 30
            clock += 300
        reading = engine.current
        assert reading is not None
        assert reading.expected_effort is not None
        self.assertTrue(reading.expectation_confident)
        self.assertAlmostEqual(reading.expected_effort, 0.88, places=2)

    def test_learned_low_load_is_not_a_learned_sleep_window(self):
        start = local_stamp("2026-10-12", 14)
        engine = AdaptiveRoutine()
        clock = 0
        for week in range(5):
            base = start + week * 7 * 86400
            engine.observe(
                Observation(base, 0.03, 4000), clock, energy=65, sleeping=False
            )
            clock += 30
            for tick in range(1, 40):
                engine.observe(
                    Observation(base + tick * 30, 0.03, 4000),
                    clock,
                    energy=65,
                    sleeping=False,
                )
                clock += 30
            clock += 500
        next_monday = start + 5 * 7 * 86400
        engine.observe(
            Observation(next_monday, 0.04, 4000), clock, energy=29, sleeping=False
        )
        clock += 30
        for tick in range(1, 34):
            engine.observe(
                Observation(next_monday + tick * 30, 0.04, 4000),
                clock,
                energy=29,
                sleeping=False,
            )
            clock += 30
        current = engine.current
        assert current is not None
        assert current.expected_effort is not None
        self.assertTrue(current.expectation_confident)
        self.assertEqual(engine.memory.quiet_window.phases, ())
        self.assertLess(current.expected_effort, 0.32)

    def test_uptime_is_context_and_never_converted_to_strain(self):
        start = local_stamp("2026-10-12", 13)
        engine = AdaptiveRoutine()
        reading = engine.observe(
            Observation(start, 0.05, 4000, uptime_hours=800),
            10,
            energy=80,
            sleeping=False,
        )
        self.assertEqual(reading.uptime_hours, 800)
        self.assertEqual(reading.strain, 0)

    def test_profile_does_not_learn_when_disabled(self):
        start = local_stamp("2026-10-12", 17)
        engine = AdaptiveRoutine()
        engine.observe(
            Observation(start, 0.8, 0), 0, energy=70, sleeping=False, learn=False
        )
        view = engine.observe(
            Observation(start + 30, 0.9, 0), 30, energy=70, sleeping=False, learn=False
        )
        self.assertEqual(sum(engine.memory.hour_seconds), 0)
        self.assertIsNone(view.expected_effort)
        self.assertGreaterEqual(view.strain, 0)

    def test_reset_learned_profile_preserves_current_stress(self):
        engine = AdaptiveRoutine()
        engine.memory.hour_seconds[10] = 123
        engine.memory.strain = 57
        engine.forget_profile()
        self.assertEqual(sum(engine.memory.hour_seconds), 0)
        self.assertEqual(engine.memory.strain, 57)

    def test_resume_from_suspend_never_retroactively_counts_as_work(self):
        start = local_stamp("2026-10-12", 12)
        engine = AdaptiveRoutine()
        engine.observe(Observation(start, 0.97, 0), 0, energy=70, sleeping=False)
        result = engine.observe(
            Observation(start + 36_000, 0.99, 9000), 36_000, energy=70, sleeping=False
        )
        self.assertEqual(result.strain, 0)
        self.assertEqual(sum(engine.memory.hour_seconds), 0)

    def test_restart_after_a_day_does_not_inherit_stale_exhaustion(self):
        start = local_stamp("2026-10-12", 13)
        memory = AdaptiveMemory(
            strain=99,
            session_seconds=20_000,
            last_session_seconds=19_000,
            last_seen_wall=start - 86400,
        )
        engine = AdaptiveRoutine(memory)
        view = engine.observe(
            Observation(start, 0.04, 5000, 800), 500, energy=75, sleeping=False
        )
        self.assertLessEqual(view.strain, 35)
        self.assertEqual(view.prolonged_work_seconds, 0)
        self.assertEqual(view.rest_seconds, 0)
        self.assertEqual(sum(memory.hour_seconds), 0)

    def test_missing_or_corrupted_fields_cannot_poison_saved_profile(self):
        loaded = AdaptiveMemory.from_dict({
            "hour_seconds": [float("nan")] * SLOTS,
            "busy_seconds": [-6] * SLOTS,
            "present_seconds": [33],
            "strain": float("inf"),
            "settled_work": "infinite",
        })
        self.assertEqual(sum(loaded.hour_seconds), 0)
        self.assertEqual(sum(loaded.busy_seconds), 0)
        self.assertEqual(sum(loaded.present_seconds), 0)
        self.assertEqual(loaded.strain, 0)
        self.assertEqual(loaded.settled_work, 0)

    def test_roundtrip_preserves_profile_and_legacy_save_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            store = StateStore(path)
            old = {
                "version": 1,
                "pet": {"mood": 47, "updated_at": 123},
                "settings": {"x": 55, "scale": 2},
            }
            path.write_text(json.dumps(old), encoding="utf-8")
            session_data = store.load_session(now=123)
            pet, config = session_data.state, session_data.settings
            memory = session_data.adaptive_memory
            self.assertEqual(pet.mood, 47)
            self.assertTrue(config.learn_rhythm)
            memory.hour_seconds[34] = 245.5
            memory.strain = 19
            save_test_session(store, pet, config, adaptive=memory)
            session_data = store.load_session(now=123)
            pet2, config2 = session_data.state, session_data.settings
            memory2 = session_data.adaptive_memory
            self.assertEqual(pet2.mood, 47)
            self.assertEqual(config2.x, 55)
            self.assertEqual(memory2.hour_seconds[34], 245.5)
            self.assertEqual(memory2.strain, 19)
            self.assertEqual(json.loads(path.read_text())["version"], 1)
            self.assertNotIn("cpu", path.read_text())

    def test_nap_fields_survive_save(self):
        state = PetState(
            sleeping=True,
            sleep_origin="nap",
            nap_until=1_800_000_000,
            auto_nap_day="2026-10-12",
            updated_at=42,
        )
        restored = decode_pet_state(encode_pet_state(state), now=42)
        self.assertEqual(restored.sleep_origin, "nap")
        self.assertEqual(restored.auto_nap_day, "2026-10-12")
        self.assertEqual(restored.nap_until, 1_800_000_000)

    def test_work_pressure_affects_emotion_only_in_context(self):
        mind = make_aiko_mind(started_at=0.0)
        base = PetState(mood=55, energy=45)
        start = local_stamp("2026-10-12", 13)
        self.assertEqual(mind.emotional_state(base).primary, EmotionalState.CALM)
        engine = AdaptiveRoutine()
        engine.memory.strain = 80
        view = engine.observe(Observation(start, 0.98, 0), 0, energy=45, sleeping=False)
        mind.set_situation(view)
        self.assertIn(
            SituationalCondition.FATIGUED,
            mind.dialogue_context(
                base, context_at(1800000000), 123
            ).situational_conditions,
        )
        mind.set_situation(None)
        self.assertEqual(mind.emotional_state(base).primary, EmotionalState.CALM)

    def test_win32_last_input_only_returns_idle_duration(self):
        def set_last_input(pointer):
            values = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32))
            values[1] = 45_000
            return 1

        def tick_count():
            return 50_000

        fake = Mock()
        fake.user32.GetLastInputInfo.side_effect = set_last_input
        fake.kernel32.GetTickCount = tick_count
        with (
            patch("aiko_pet.desktop.global_input.sys.platform", "win32"),
            patch("aiko_pet.desktop.global_input.ctypes.windll", fake, create=True),
        ):
            self.assertEqual(idle_seconds_windows(), 5.0)

    def test_win32_idle_wraparound_is_unsigned(self):
        def set_last_input(pointer):
            values = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32))
            values[1] = 0xFFFF_FF00
            return 1

        def tick_count():
            return 0x0000_0300

        fake = Mock()
        fake.user32.GetLastInputInfo.side_effect = set_last_input
        fake.kernel32.GetTickCount = tick_count
        with (
            patch("aiko_pet.desktop.global_input.sys.platform", "win32"),
            patch("aiko_pet.desktop.global_input.ctypes.windll", fake, create=True),
        ):
            elapsed = idle_seconds_windows()
            assert elapsed is not None
            self.assertAlmostEqual(elapsed, 1.024)

    def test_idle_reading_unavailable_outside_windows(self):
        with patch("aiko_pet.desktop.global_input.sys.platform", "linux"):
            self.assertIsNone(idle_seconds_windows())


if __name__ == "__main__":
    unittest.main()
