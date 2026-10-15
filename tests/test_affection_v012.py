"""Distinct affection need, meaningful trust rewards and backwards-compatible saves."""

from __future__ import annotations

import json
import random
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.catalog import DialogueBook, Reaction
from aiko_pet.pet.friendship import FRIENDSHIP_DAILY_CAP
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.state import PetState
from aiko_pet.pet.status_hints import MoodHint
from aiko_pet.ui.view_models.text_de import mood_hint_text, format_emotion_label
from aiko_pet.pet.routine import context_at
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore


def require_reaction(value: Reaction | None) -> Reaction:
    """Fail immediately if an expected authored dialogue is unavailable."""
    assert value is not None, "Expected a dialogue reaction"
    return value


def stamp(day: str = "2026-10-12", hour: int = 12) -> float:
    return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone().timestamp()


class AffectionNeedTests(unittest.TestCase):
    def test_pet_primarily_refills_affection_and_never_gives_energy(self):
        state = PetState(affection=30, mood=25, social=40, energy=50)
        state.interact("pet", now=stamp())
        self.assertEqual(state.affection, 55)
        self.assertGreater(state.mood, 25)
        self.assertEqual(state.social, 42)
        self.assertEqual(state.energy, 50)

    def test_completed_play_is_fun_and_company_not_affection(self):
        state = PetState(
            affection=17, mood=35, social=18, energy=50,
            satiety=50, fun=25,
        )
        state.record_game_experience(
            GameExperience(
                "rock_paper_scissors", 3, successful_units=2, setback_units=1,
            ),
            now=stamp(),
        )
        self.assertGreater(state.fun, 25)
        self.assertGreater(state.social, 18)
        self.assertLess(state.energy, 50)
        self.assertEqual((state.affection, state.satiety), (17, 50))

    def test_talking_improves_social_not_affection(self):
        state = PetState(affection=21, social=19, mood=32)
        state.interact("talk", now=stamp())
        self.assertEqual(state.social, 45)
        self.assertGreater(state.mood, 32)
        self.assertEqual(state.affection, 21)

    def test_food_and_energy_drinks_do_not_refill_affection(self):
        state = PetState(affection=16, satiety=23, energy=30)
        state.interact("feed", now=stamp())
        state.interact("energy_drink", now=stamp() + 1)
        self.assertEqual(state.affection, 16)
        self.assertEqual(state.energy, 40)

    def test_affection_decays_gently_even_under_heavy_work(self):
        start = stamp()
        idle = PetState(updated_at=start, affection=55, social=50)
        working = PetState(updated_at=start, affection=55, social=50)
        for minute in range(1, 121):
            point = start + minute * 60
            idle.advance(point, effort=0.0)
            working.advance(point, effort=1.0)
        self.assertAlmostEqual(idle.affection, working.affection)
        self.assertAlmostEqual(idle.affection, 55 - 2 * 6, places=2)
        self.assertLess(working.energy, idle.energy)
        self.assertLess(working.satiety, idle.satiety)

    def test_affection_slowly_declines_during_sleep_without_affecting_trust(self):
        start = stamp()
        state = PetState(updated_at=start, affection=30, friendship=63,
                         sleeping=True, sleep_origin="manual")
        state.advance(start + 2 * 3600, effort=1.0)
        self.assertAlmostEqual(state.affection, 29.5, places=2)
        self.assertEqual(state.friendship, 63)

    def test_low_affection_has_gentle_mood_effect_distinct_from_social(self):
        start = stamp()
        comfortable = PetState(updated_at=start, affection=40, social=50)
        under_cared = PetState(updated_at=start, affection=15, social=50)
        comfortable.advance(start + 3600)
        under_cared.advance(start + 3600)
        self.assertLess(under_cared.mood, comfortable.mood)
        self.assertAlmostEqual(under_cared.social, comfortable.social)

    def test_affection_need_is_clamped_and_status_hint_is_distinct(self):
        state = PetState.from_dict({"affection": "nan", "social": 80}, now=stamp())
        self.assertEqual(state.affection, 75)
        affection_hint = PetState(affection=5).mood_hint()
        social_hint = PetState(social=5, affection=85).mood_hint()
        self.assertIs(affection_hint, MoodHint.NEEDS_AFFECTION)
        self.assertIs(social_hint, MoodHint.LONELY)
        self.assertIn("Geste", mood_hint_text(affection_hint))
        self.assertIn("Gesellschaft", mood_hint_text(social_hint))
        self.assertEqual(PetState.from_dict({"affection": -7}).affection, 0)
        self.assertEqual(PetState.from_dict({"affection": 700}).affection, 100)


class MeaningfulFriendshipTests(unittest.TestCase):
    def test_care_on_an_already_full_primary_need_does_not_farm_trust(self):
        for action, value in (("feed", "satiety"), ("pet", "affection"),
                              ("talk", "social"), ("play", "fun")):
            with self.subTest(action=action):
                state = PetState(energy=60)
                setattr(state, value, 100)
                state.interact(action, now=stamp())
                self.assertEqual(state.friendship, 15)

    def test_first_useful_care_rewards_friendship_but_spam_does_not(self):
        state = PetState(affection=25)
        state.interact("pet", now=stamp())
        self.assertEqual(state.friendship, 16)
        for i in range(40):
            state.interact("pet", now=stamp() + i + 1)
        self.assertEqual(state.friendship, 16)
        # Even after the reward cooldown, full affection is not useful care.
        state.interact("pet", now=stamp() + 20 * 60)
        self.assertEqual(state.friendship, 16)
        state.affection = 40
        state.interact("pet", now=stamp() + 21 * 60)
        self.assertGreater(state.friendship, 16)

    def test_diverse_care_is_more_effective_than_repeating_one_action(self):
        diverse = PetState(affection=20, mood=20, social=20, satiety=20, energy=70)
        repeated = PetState(affection=20, mood=20, social=20, satiety=20, energy=70)
        start = stamp()
        for action in ("feed", "pet", "talk"):
            diverse.interact(action, now=start)
        diverse.record_game_experience(
            GameExperience("rock_paper_scissors", 2, successful_units=1),
            now=start,
        )
        for i in range(4):
            repeated.affection = 20
            repeated.interact("pet", now=start + i * 15 * 60)
        self.assertGreater(diverse.friendship, repeated.friendship)
        self.assertEqual(set(diverse.care_types_today), {"feed", "pet", "talk", "play"})

    def test_drinks_and_sleep_do_not_build_friendship_by_button_mashing(self):
        state = PetState(energy=0, friendship=42)
        for i in range(10):
            state.interact("energy_drink", now=stamp() + i)
        state.interact("sleep", now=stamp() + 15)
        state.interact("sleep", now=stamp() + 16)
        self.assertEqual(state.friendship, 42)
        self.assertEqual(state.energy, 100)

    def test_bond_is_capped_per_day_then_can_progress_next_day(self):
        start = stamp()
        state = PetState(affection=0, social=0, mood=0, satiety=0, energy=65)
        for i in range(20):
            for action, attribute in (("feed", "satiety"),
                                      ("pet", "affection"),
                                      ("talk", "social"),
                                      ("play", "fun")):
                setattr(state, attribute, 20)
                state.energy = 65
                state.interact(action, now=start + 16 * 60 * i)
        self.assertLessEqual(state.friendship, 15 + FRIENDSHIP_DAILY_CAP + 1e-6)
        previous = state.friendship
        state.social = 20
        state.interact("talk", now=stamp("2026-10-13"))
        self.assertGreater(state.friendship, previous)
        self.assertEqual(state.care_types_today, ["talk"])

    def test_old_save_preserves_existing_relationship_and_needs(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp)/"pet.json")
            store.path.write_text(json.dumps({
                "version": 1,
                "pet": {"satiety": 30, "mood": 60, "energy": 40,
                        "social": 24, "friendship": 54, "updated_at": stamp(),
                        "care_last_rewards": {"pet": stamp()-300,
                                              "sleep": stamp()-400}},
                "settings": {"scale": 2, "toolbar_x": 120, "toolbar_y": 70},
            }), encoding="utf8")
            state, settings = store.load(now=stamp())
            self.assertEqual((state.satiety, state.mood, state.energy,
                              state.social, state.affection, state.friendship),
                             (30, 60, 40, 24, 75, 54))
            self.assertEqual((settings.scale, settings.toolbar_x,
                              settings.toolbar_y), (2, 120, 70))
            self.assertIn("sleep", state.care_last_rewards)
            store.save(state, settings)
            again, _ = store.load(now=stamp())
            self.assertEqual(again.affection, 75)
            self.assertEqual(again.friendship, 54)

    def test_new_relationship_metadata_survives_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp)/"pet.json")
            state = PetState(updated_at=stamp(), affection=35)
            state.interact("pet", now=stamp())
            state.social = 35
            state.interact("talk", now=stamp()+1)
            store.save(state, PetSettings())
            restored, _ = store.load(now=stamp()+1)
            self.assertEqual(restored.care_types_today, ["pet", "talk"])
            self.assertEqual(restored.care_last_rewards,
                             state.care_last_rewards)
            self.assertEqual(restored.friendship, state.friendship)
            self.assertAlmostEqual(restored.affection, state.affection, places=2)
            raw = store.path.read_text(encoding="utf8")
            for secret in ('"cpu"', '"gpu"', '"ram"', '"keys"'):
                self.assertNotIn(secret, raw)

    def test_corrupt_daily_action_list_is_sanitized(self):
        state = PetState.from_dict({
            "care_types_today": ["pet", "pet", "other", 10, "talk"],
            "affection": 12, "friendship_gained_today": 999,
        })
        self.assertEqual(state.care_types_today, ["pet", "talk"])
        self.assertEqual(state.friendship_gained_today, FRIENDSHIP_DAILY_CAP)


class AffectionDialogueTests(unittest.TestCase):
    def setUp(self):
        self.mind = make_aiko_mind(started_at=0.0, rng=random.Random(12))
        self.context = context_at(stamp())

    def test_low_affection_is_not_social_loneliness(self):
        state = PetState(social=70, affection=12)
        self.assertEqual(self.mind.emotion(state, 50), "seeking_affection")
        self.assertEqual(
            format_emotion_label("seeking_affection"),
            "Stimmung: Wünscht Zuwendung",
        )
        self.assertEqual(require_reaction(self.mind.click("left", state, self.context, 50)).event,
                         "click_affection_low")
        self.assertEqual(self.mind.care_event("pet", state, self.context, 55)[0],
                         "pet_needs_affection")
        self.assertEqual(self.mind.care_event("talk", state, self.context, 55)[0],
                         "talk")

    def test_existing_social_shortage_still_has_own_priority(self):
        state = PetState(social=10, affection=10)
        self.assertEqual(self.mind.emotion(state, 50), "lonely")
        self.assertEqual(require_reaction(self.mind.click("left", state, self.context, 50)).event,
                         "click_lonely")

    def test_feeling_cared_for_can_make_aiko_more_at_ease(self):
        state = PetState(affection=95, friendship=55, mood=73, social=78)
        self.assertEqual(
            require_reaction(self.mind.click("left", state, self.context, 50)).event,
            "click_at_ease",
        )
        reserved = make_aiko_mind(started_at=0.0, rng=random.Random(12))
        state.affection = 50
        self.assertEqual(
            require_reaction(reserved.click("left", state, self.context, 50)).event,
            "click_left",
        )

    def test_affection_spontaneous_hint_has_long_cooldown(self):
        state = PetState(affection=8)
        self.assertEqual(require_reaction(self.mind.spontaneous_event(
            state, self.context, 60)).event, "affection_low")
        self.assertEqual(require_reaction(self.mind.spontaneous_event(
            state, self.context, 61)).event, "idle")
        self.assertEqual(require_reaction(self.mind.spontaneous_event(
            state, self.context, 60 + 26 * 60)).event, "affection_low")

    def test_dialogues_all_use_existing_sprites_and_grounded_topics(self):
        lines = [line for line in DialogueBook.from_file().lines
                 if line.id.startswith("v012-")]
        self.assertGreaterEqual(len(lines), 12)
        self.assertEqual({line.event for line in lines},
                         {"affection_low", "click_affection_low",
                          "pet_needs_affection", "click_at_ease"})
        self.assertTrue(all(line.animation in {
            "idle", "waiting", "review", "failed", "jumping", "waving"
        } for line in lines))
        self.assertTrue(all("CPU" not in line.text and "Academy" not in line.text
                            for line in lines))


if __name__ == "__main__":
    unittest.main()
