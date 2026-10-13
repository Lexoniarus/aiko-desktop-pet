"""Checks for weekday/weekend care timing without story-world obligations."""

import unittest
from datetime import datetime

from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import context_at


def local_time(day, hour, minute=0):
    return datetime.fromisoformat(f"{day}T{hour:02d}:{minute:02d}:00").astimezone().timestamp()


class DailyRoutineTests(unittest.TestCase):
    def test_weekday_quiet_morning_and_meal_windows(self):
        self.assertEqual(context_at(local_time("2026-10-12", 8)).meal, "breakfast")
        morning = context_at(local_time("2026-10-12", 10))
        self.assertEqual(morning.period, "quiet")
        self.assertFalse(morning.weekend)
        self.assertIn("Ruhiger Vormittag", morning.label)
        self.assertNotIn("Academy", morning.label)
        self.assertEqual(context_at(local_time("2026-10-12", 13)).meal, "lunch")
        self.assertEqual(context_at(local_time("2026-10-12", 19)).meal, "dinner")
        self.assertTrue(context_at(local_time("2026-10-12", 23, 45)).night)
        self.assertIn("Dienstag", context_at(local_time("2026-10-13", 10)).label)

    def test_saturday_has_later_meals_and_more_freetime(self):
        self.assertTrue(context_at(local_time("2026-10-17", 8, 30)).night)
        breakfast = context_at(local_time("2026-10-17", 9, 5))
        self.assertTrue(breakfast.weekend)
        self.assertEqual(breakfast.meal, "breakfast")
        self.assertEqual(context_at(local_time("2026-10-17", 12)).period, "free")
        self.assertEqual(context_at(local_time("2026-10-17", 14)).meal, "lunch")
        self.assertFalse(context_at(local_time("2026-10-17", 23, 50)).night)
        self.assertTrue(context_at(local_time("2026-10-18", 0, 5)).night)
        self.assertTrue(context_at(local_time("2026-10-18", 23, 45)).night)

    def test_night_key_does_not_reset_at_midnight(self):
        self.assertEqual(
            context_at(local_time("2026-10-18", 23, 30)).night_key,
            context_at(local_time("2026-10-19", 2)).night_key,
        )
        self.assertEqual(
            context_at(local_time("2026-10-16", 23, 30)).night_key,
            context_at(local_time("2026-10-17", 2)).night_key,
        )

    def test_automatic_bedtime_and_wakeup_with_overnight_catchup(self):
        start = local_time("2026-10-12", 23, 20)
        state = PetState(energy=20, updated_at=start)
        state.advance(local_time("2026-10-12", 23, 55), auto_routine=True)
        self.assertTrue(state.sleeping)
        self.assertEqual(state.sleep_origin, "routine")
        state.advance(local_time("2026-10-13", 7, 45), auto_routine=True)
        self.assertFalse(state.sleeping)
        self.assertGreater(state.energy, 90)
        self.assertGreater(state.satiety, 50)

    def test_manual_wake_stays_respected_until_next_night(self):
        state = PetState(updated_at=local_time("2026-10-12", 23, 20))
        state.advance(local_time("2026-10-12", 23, 55), auto_routine=True)
        self.assertTrue(state.sleeping)
        state.interact("sleep", now=local_time("2026-10-12", 23, 58))
        self.assertFalse(state.sleeping)
        state.advance(local_time("2026-10-13", 0, 10), auto_routine=True)
        self.assertFalse(state.sleeping)
        state.advance(local_time("2026-10-13", 23, 55), auto_routine=True)
        self.assertTrue(state.sleeping)

    def test_manual_nap_is_not_automatically_cancelled(self):
        state = PetState(updated_at=local_time("2026-10-12", 12))
        state.interact("sleep")
        state.advance(local_time("2026-10-12", 14, 30), auto_routine=True)
        self.assertTrue(state.sleeping)
        self.assertEqual(state.sleep_origin, "manual")

    def test_meals_are_only_recorded_once_per_local_day(self):
        morning = local_time("2026-10-17", 9, 20)
        state = PetState(updated_at=morning)
        context = context_at(morning)
        self.assertEqual(state.feed_label(context), "Frühstück")
        response = state.interact("feed", now=morning)
        self.assertIn("frühstück", response)
        self.assertEqual(state.feed_label(context), "Snack")
        self.assertEqual(state.meals_today, ["breakfast"])
        state.interact("feed", now=morning)
        self.assertEqual(state.meals_today, ["breakfast"])
        state.advance(local_time("2026-10-18", 9, 20), auto_routine=True)
        self.assertEqual(state.feed_label(context_at(local_time("2026-10-18", 9, 20))), "Frühstück")
        self.assertEqual(state.meals_today, [])

    def test_weekend_keeps_hourly_care_rhythm(self):
        weekday = PetState(updated_at=local_time("2026-10-12", 14), mood=50)
        weekend = PetState(updated_at=local_time("2026-10-17", 15), mood=50)
        weekday.advance(local_time("2026-10-12", 16), auto_routine=True)
        weekend.advance(local_time("2026-10-17", 17), auto_routine=True)
        self.assertLess(weekend.mood, 50)
        self.assertAlmostEqual(weekend.mood, weekday.mood)
        self.assertAlmostEqual(weekday.energy, weekend.energy)

    def test_auto_routine_can_be_switched_off(self):
        state = PetState(updated_at=local_time("2026-10-12", 22, 55))
        state.advance(local_time("2026-10-12", 23, 15), auto_routine=False)
        self.assertFalse(state.sleeping)
        self.assertEqual(state.energy, 75 - 6 / 3)

    def test_legacy_sleep_is_treated_as_manual(self):
        state = PetState.from_dict({"sleeping": True, "updated_at": local_time("2026-10-12", 9)})
        self.assertEqual(state.sleep_origin, "manual")
        state.advance(local_time("2026-10-12", 10), auto_routine=True)
        self.assertTrue(state.sleeping)


if __name__ == "__main__":
    unittest.main()
