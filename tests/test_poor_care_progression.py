"""Poor-care triggers share real need chronology, storage and elapsed time."""

import copy
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
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.friendship_history import NEED_NAMES
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import MoodletId, reinforce_moodlet
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session

WALL = 1_800_000_000.0


def pet(**values):
    return PetState(updated_at=WALL, **{**dict.fromkeys(NEED_NAMES, 100), **values})


class PoorCareProgressionTests(unittest.TestCase):
    def test_each_need_creates_its_own_after_effect_from_real_zero_exposure(self):
        for name, key in zip(NEED_NAMES, (
            MoodletId.HUNGER_WORN, MoodletId.EXHAUSTION_IRRITATED,
            MoodletId.UNSTIMULATED, MoodletId.LONELY, MoodletId.MISSING_CLOSENESS,
        ), strict=True):
            with self.subTest(need=name):
                state = pet(**{name: 0})
                state.advance(WALL + 3599)
                self.assertFalse(state.moodlets.active)
                mood = state.mood
                state.advance(WALL + 3600)
                episode = state.moodlets.active[0]
                self.assertEqual((episode.definition_id, episode.level), (key, 1))
                self.assertAlmostEqual(episode.started_at, 3600, places=5)
                self.assertLessEqual(abs(state.mood - mood), .15)  # No instant -5.

    def test_clamped_zero_crossing_counts_only_actual_zero_time(self):
        state = pet(energy=.01)
        state.advance(WALL + 3611.9)
        self.assertFalse(state.moodlets.active)
        state.advance(WALL + 3612)
        episode = state.moodlets.active[0]
        self.assertEqual(episode.definition_id, MoodletId.EXHAUSTION_IRRITATED)
        self.assertAlmostEqual(episode.started_at, 3612, places=4)

    def test_split_calls_and_save_reload_keep_the_same_threshold_and_burden(self):
        whole = pet(satiety=25.02)
        divided = copy.deepcopy(whole)
        whole.advance(WALL + 4 * 3600, observed=False)
        for seconds in (113.4, 3599.8, 7200.1, 10001, 14400):
            divided.advance(WALL + seconds, observed=False)
            divided = decode_pet_state(
                encode_pet_state(divided), now=divided.updated_at,
            )
        self.assertEqual([e.definition_id for e in divided.moodlets.active],
                         [e.definition_id for e in whole.moodlets.active])
        for actual, expected in zip(divided.moodlets.active, whole.moodlets.active,
                                    strict=True):
            self.assertEqual(actual.level, expected.level)
            self.assertAlmostEqual(actual.started_at, expected.started_at, places=4)
            self.assertAlmostEqual(actual.last_trigger_at, expected.last_trigger_at,
                                   places=4)
        # The existing save codec quantizes numeric friendship to four decimals.
        self.assertAlmostEqual(divided.friendship, whole.friendship, delta=.0001)
        self.assertAlmostEqual(divided.mood, whole.mood, delta=.05)

    def test_closed_and_standby_share_after_effects_without_replaying_on_reopen(self):
        original = pet(satiety=0)
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            settings = PetSettings(auto_routine=False)
            save_test_session(store, original, settings)
            closed = PetSessionRestorer(store, wall_time=lambda: WALL + 7200).restore()
            uptime = [0.0]
            clock = ActiveSessionClock(lambda: uptime[0])
            uptime[0] = 7200
            advance_session_time(original, clock, SessionInputs(
                WALL + 7200, 0, False, None, False, False, None,
            ))
            self.assertEqual(original.capture_checkpoint(),
                             closed.state.capture_checkpoint())
            self.assertEqual(closed.state.moodlets.active[0].level, 2)
            save_test_session(store, closed.state, settings)
            reopened = PetSessionRestorer(
                store, wall_time=lambda: WALL + 7200,
            ).restore()
            self.assertEqual(encode_pet_state(reopened.state),
                             encode_pet_state(closed.state))

    def test_capped_poor_care_does_not_freeze_other_moodlets_or_block_help(self):
        state = pet(**dict.fromkeys(NEED_NAMES, 0))
        state.advance(WALL + 3 * 3600)
        self.assertEqual(len(state.moodlets.active), 5)
        checkpoint = state.capture_checkpoint()
        positive = reinforce_moodlet(state.moodlets, MoodletId.PRIDE,
                                     elapsed=state.lived_seconds,
                                     definitions=MOODLET_CATALOG.definitions)
        positive = replace(positive, active=tuple(
            replace(e, remaining_seconds=100)
            if e.definition_id == MoodletId.PRIDE else e
            for e in positive.active
        ))
        state.restore_checkpoint(replace(checkpoint, moodlets=positive))
        state.advance(WALL + 3 * 3600 + 120)
        self.assertNotIn(MoodletId.PRIDE,
                         [e.definition_id for e in state.moodlets.active])
        self.assertEqual(len(state.moodlets.active), 5)
        result = state.interact("feed", now=state.updated_at)
        self.assertTrue(result.food_consumed)
        self.assertGreater(state.satiety, 0)
        self.assertEqual(len(state.moodlets.active), 5)
