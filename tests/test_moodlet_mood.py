"""Capped emotional contributions use the real need target and response rates."""

from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
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
from aiko_pet.pet.mood import NeedMoodFactors, calculate_mood_target
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletContributions,
    MoodletEpisode,
    MoodletGroup,
    MoodletId,
    MoodletState,
    calculate_moodlet_contributions,
)
from aiko_pet.pet.progression import calculate_pet_progression
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import WorldSurface
from aiko_pet.world.state import WorldState
from tools.pet_test_support import require_test_value

WALL = 1_800_000_000.0
DEFINITIONS = MOODLET_CATALOG.definitions


def seeded_pet(key=MoodletId.FOOD_FULFILLED, level=1, remaining=5, **values):
    return PetState(updated_at=WALL, satiety=100, energy=100, fun=100,
                    social=100, affection=100, mood=84, moodlets=MoodletState(0, 2, (
                        MoodletEpisode(1, key, level, 0, 0, remaining),
                    )), **values)


class MoodletMoodTests(unittest.TestCase):
    def test_group_caps_precede_separate_global_caps_without_removing_entries(self):
        episodes = tuple(MoodletEpisode(i, d.id, len(d.level_points), 0, 0,
                                       d.decay_stage_seconds)
                         for i, d in enumerate(DEFINITIONS.values(), 1))
        state = MoodletState(0, len(episodes) + 1, episodes)
        contributions = calculate_moodlet_contributions(
            state, definitions=DEFINITIONS,
            long_term_policy=MOODLET_CATALOG.long_term_policy,
        )
        self.assertEqual(contributions, MoodletContributions(20, -30))
        self.assertEqual(
            tuple(e.definition_id for e in state.active), tuple(DEFINITIONS),
        )
        for group, expected in ((MoodletGroup.GAME_WISH, (15, 0)),
                                (MoodletGroup.SOCIAL_WISH, (15, 0)),
                                (MoodletGroup.POOR_CARE, (0, -15))):
            subset = replace(state, active=tuple(e for e in episodes
                                                if DEFINITIONS[e.definition_id].group
                                                == group))
            self.assertEqual(calculate_moodlet_contributions(
                subset, definitions=DEFINITIONS,
                long_term_policy=MOODLET_CATALOG.long_term_policy,
            ), MoodletContributions(*expected))

    def test_final_composition_retains_zero_need_ceiling_and_clamps_to_zero(self):
        factors = NeedMoodFactors(100, 100, 100, 100, 100)
        self.assertEqual(calculate_mood_target(factors), 80)
        self.assertEqual(calculate_mood_target(factors, MoodletContributions(20)), 100)
        self.assertEqual(calculate_mood_target(factors,
                                              MoodletContributions(20, -30)), 70)
        self.assertEqual(calculate_mood_target(replace(factors, satiety=0),
                                              MoodletContributions(20)), 30)
        self.assertEqual(calculate_mood_target(NeedMoodFactors(0, 0, 0, 0, 0),
                                              MoodletContributions(0, -30)), 0)

    def test_expiry_inside_a_step_uses_old_effect_until_the_actual_boundary(self):
        for level, initial_mood in ((1, 84), (2, 89)):
            pet = seeded_pet(MoodletId.PRIDE, level=level)
            pet.restore_checkpoint(replace(pet.capture_checkpoint(), mood=initial_mood))
            split = deepcopy(pet)
            pet.advance(WALL + 15, observed=False)
            split.advance(WALL + 5, observed=False)
            split.advance(WALL + 15, observed=False)
            self.assertAlmostEqual(pet.mood, initial_mood)
            self.assertEqual(pet.capture_checkpoint(), split.capture_checkpoint())
            if level == 1:
                self.assertEqual(pet.moodlets.active, ())
            else:
                self.assertEqual((pet.moodlets.active[0].level,
                                  pet.moodlets.active[0].remaining_seconds), (1, 7190))

    def test_actual_mood_changes_over_time_not_on_target_composition(self):
        pet = seeded_pet(remaining=7200)
        before = pet.capture_checkpoint()
        progress = calculate_pet_progression(pet, 30 / 3600)
        self.assertEqual(pet.capture_checkpoint(), before)
        self.assertGreater(progress.mood, pet.mood)
        self.assertLessEqual(progress.mood, pet.mood + 1)
        self.assertEqual(progress.moodlets.active[0].remaining_seconds, 7170)

    def test_sleep_recovery_qualifies_at_40_then_waits_thirty_minutes(self):
        pet = seeded_pet(MoodletId.EXHAUSTION_IRRITATED, level=2, remaining=7200)
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), energy=39.99,
                                       sleeping=True, sleep_origin="manual"))
        split = deepcopy(pet)
        pet._advance_progression(1824 / 3600, observed=False)
        for _ in range(1824):
            split._advance_progression(1 / 3600, observed=False)
        episode = pet.moodlets.active[0]
        # Sleep restores 7.5 energy/hour: crossing 40 takes 4.8 seconds.
        assert episode.recovery_since is not None
        self.assertAlmostEqual(episode.recovery_since, 4.8, places=6)
        self.assertAlmostEqual(episode.remaining_seconds, 7180.8, places=6)
        self.assertAlmostEqual(split.moodlets.active[0].remaining_seconds,
                               episode.remaining_seconds, places=5)
        self.assertAlmostEqual(split.mood, pet.mood, delta=.05)

    def test_falling_below_40_pauses_at_the_crossing_not_at_step_end(self):
        pet = seeded_pet(MoodletId.LONELY, remaining=100)
        episode = replace(pet.moodlets.active[0], recovery_since=0)
        pet.restore_checkpoint(replace(
            pet.capture_checkpoint(), social=40.01, lived_seconds=1800,
            moodlets=replace(pet.moodlets, active=(episode,)),
        ))
        pet._advance_progression(15 / 3600)
        stored = pet.moodlets.active[0]
        # Social falls eight points/hour while awake: 0.01 takes 4.5 seconds.
        self.assertAlmostEqual(stored.remaining_seconds, 95.5, places=6)
        self.assertTrue(stored.decay_paused)
        self.assertIsNone(stored.recovery_since)
        self.assertEqual(decode_pet_state(encode_pet_state(pet), now=WALL).moodlets,
                         pet.moodlets)

    def test_closed_and_standby_paths_age_once_with_the_same_unknown_interval(self):
        for key in (MoodletId.POKING, MoodletId.PRIDE):
            original = seeded_pet(key, level=3, remaining=1195)
            if key == MoodletId.PRIDE:
                original.restore_checkpoint(replace(
                    original.capture_checkpoint(),
                    moodlets=replace(original.moodlets, active=(
                        replace(original.moodlets.active[0],
                                lower_stage_seconds=(3600, 2700)),
                    )),
                ))
            with tempfile.TemporaryDirectory() as folder:
                store = StateStore(Path(folder) / "state.json")
                settings = PetSettings(auto_routine=False)
                store.save(original, settings)
                closed = PetSessionRestorer(
                    store, wall_time=lambda: WALL + 3600,
                ).restore()
                uptime = [10.0]
                clock = ActiveSessionClock(lambda: uptime[0])
                uptime[0] += 3600
                advance_session_time(original, clock, SessionInputs(
                    WALL + 3600, 0, False, None, False, False, None,
                ))
                self.assertEqual(original.capture_checkpoint(),
                                 closed.state.capture_checkpoint())
                if key == MoodletId.PRIDE:
                    self.assertEqual(original.moodlets.active[0].level, 2)
                    self.assertEqual(original.moodlets.active[0].remaining_seconds, 295)
                    self.assertEqual(original.moodlets.active[0].lower_stage_seconds,
                                     (3600,))
                else:
                    self.assertEqual(original.moodlets.active, ())
                store.save(closed.state, settings)
                again = PetSessionRestorer(
                    store, wall_time=lambda: WALL + 3600,
                ).restore()
                self.assertEqual(encode_pet_state(again.state),
                                 encode_pet_state(closed.state))
                self.assertEqual(again.state.lived_seconds, 3600)

    def test_short_closed_interval_never_continues_observed_withholding(self):
        for with_world in (False, True):
            pet = seeded_pet(MoodletId.WITHHELD, remaining=1200)
            paused = replace(pet.moodlets.active[0], decay_paused=True)
            pet.restore_checkpoint(replace(
                pet.capture_checkpoint(),
                moodlets=replace(pet.moodlets, active=(paused,)),
            ))
            with tempfile.TemporaryDirectory() as folder:
                store = StateStore(Path(folder) / "state.json")
                world = WorldState(WorldSurface(800, 600), ()) if with_world else None
                store.save(pet, PetSettings(auto_routine=False),
                           world=world.snapshot() if world else None)
                loaded = PetSessionRestorer(
                    store, wall_time=lambda: WALL + 10,
                ).restore()
                episode = loaded.state.moodlets.active[0]
                self.assertEqual(episode.remaining_seconds, 1190)
                self.assertFalse(loaded.state.moodlets.active[0].decay_paused)

    def test_world_time_uses_the_same_domain_calculation(self):
        pet = seeded_pet(MoodletId.PRIDE, level=2, remaining=5)
        world = WorldState(WorldSurface(800, 600), ())
        memory = ObjectMemory()
        expected = deepcopy(pet)
        expected.advance(WALL + 15, observed=False)
        SessionTimeProgression(world, memory).advance(pet, SessionInputs(
            WALL + 15, 0, False, None, False, False, None,
        ), 15, reconstruct=True)
        self.assertEqual(pet.capture_checkpoint(), expected.capture_checkpoint())

    def test_full_day_expires_short_families_and_qualifies_actual_contact_gap(self):
        episodes = tuple(MoodletEpisode(i, d.id, len(d.level_points), 0, 0,
                                       d.decay_stage_seconds)
                         for i, d in enumerate(DEFINITIONS.values(), 1)
                         if d.group != MoodletGroup.LONG_TERM)
        next_id = max(e.instance_id for e in episodes) + 1
        pet = PetState(updated_at=WALL, satiety=0, energy=0, social=0,
                       affection=0, fun=0, mood=0,
                       moodlets=MoodletState(0, next_id, episodes))
        pet.advance(WALL + 86400, observed=False)
        self.assertEqual({e.definition_id for e in pet.moodlets.active}, {
            d.id for d in DEFINITIONS.values() if d.group == MoodletGroup.POOR_CARE
        } | {MoodletId.OVERLOOKED})
        self.assertEqual(pet.moodlets.next_instance_id, next_id + 1)
        self.assertTrue(all(e.decay_paused for e in pet.moodlets.active
                            if e.definition_id != MoodletId.OVERLOOKED))
        overlooked = next(e for e in pet.moodlets.active
                          if e.definition_id == MoodletId.OVERLOOKED)
        self.assertFalse(overlooked.decay_paused)
        self.assertEqual(require_test_value(overlooked.causes[0].period).encounters, 0)
        self.assertEqual(
            require_test_value(overlooked.causes[0].period).awake_contact_gap_seconds,
            86400,
        )
        self.assertFalse(require_test_value(pet.moodlets.care_evidence).experiences)
        self.assertEqual(pet.mood, 0)
        self.assertEqual(pet.lived_seconds, 86400)
