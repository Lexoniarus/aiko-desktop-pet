"""Fractional clock intervals stay coherent through policies and strict saves."""

from __future__ import annotations

import math
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
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import SaveRevision
from aiko_pet.infrastructure.friendship_codec import (
    decode_friendship,
    encode_friendship,
)
from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.infrastructure.sleep_codec import decode_sleep, encode_sleep
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.infrastructure.wish_codec import decode_wishes, encode_wishes
from aiko_pet.pet.friendship_history import FriendshipHistory
from aiko_pet.pet.lifecycle import plan_pet_time
from aiko_pet.pet.long_term_moodlets import prepare_long_term
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.sleep import SleepContext, SleepEpisode
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.world.contracts import WorldSurface
from aiko_pet.world.state import WorldState

WALL = 1_800_000_000.0


def validate_time_evidence(pet: PetState) -> None:
    elapsed = pet.lived_seconds
    decode_friendship(encode_friendship(pet.friendship_history), elapsed)
    decode_moodlets(encode_moodlets(pet.moodlets), elapsed)
    decode_sleep(encode_sleep(pet.sleep_episode), elapsed)
    decode_wishes(encode_wishes(pet.wishes), elapsed)


class TimeContractTests(unittest.TestCase):
    def test_plan_preserves_fractional_and_sub_wall_precision_intervals(self) -> None:
        for start in (0.0, 467390.5999761847):
            for duration in (1e-10, 0.016, 29.999, 55.123456789):
                for routine in (False, True):
                    with self.subTest(start=start, duration=duration, routine=routine):
                        plan = plan_pet_time(
                            WALL,
                            WALL + duration,
                            elapsed_seconds=duration,
                            elapsed_start=start,
                            auto_routine=routine,
                        )
                        assert plan is not None
                        steps = list(plan)
                        self.assertEqual(plan.elapsed_end, start + duration)
                        if plan.elapsed_end == start:
                            self.assertEqual(steps, [])
                            continue
                        self.assertEqual(steps[0].elapsed_start, start)
                        self.assertEqual(steps[-1].elapsed_end, plan.elapsed_end)
                        self.assertEqual(steps[-1].wall_end, plan.now)
                        self.assertEqual(
                            math.fsum(s.seconds for s in steps),
                            plan.elapsed_end - start,
                        )
                        for left, right in zip(steps, steps[1:]):
                            self.assertEqual(left.elapsed_end, right.elapsed_start)
                            self.assertEqual(left.wall_end, right.wall_start)

    def test_direct_and_world_paths_keep_all_evidence_valid_through_save_restart(
        self,
    ) -> None:
        for start in (0.0, 467390.5999761847):
            for sleeping in (False, True):
                for with_world in (False, True):
                    with (
                        self.subTest(
                            start=start, sleeping=sleeping, with_world=with_world
                        ),
                        tempfile.TemporaryDirectory(prefix="aiko-time-contract-") as d,
                    ):
                        pet = PetState(
                            updated_at=WALL,
                            lived_seconds=start,
                            energy=39.99,
                            satiety=75 if sleeping else 0,
                            affection=75 if sleeping else 0,
                            sleeping=sleeping,
                            sleep_origin="manual" if sleeping else "",
                            sleep_episode=SleepEpisode(
                                "main",
                                start,
                                0,
                                WALL + 8 * 3600,
                                start + 300,
                            )
                            if sleeping
                            else None,
                            wishes=WishState(
                                2,
                                (
                                    ActiveWish(
                                        1, WishId.PET, "pet", start, start + 0.04
                                    ),
                                ),
                                ((WishArea.AFFECTION, start),),
                            ),
                            moodlets=MoodletState(
                                start,
                                2,
                                (
                                    MoodletEpisode(
                                        1,
                                        MoodletId.EXHAUSTION_IRRITATED,
                                        1,
                                        start,
                                        start,
                                        7200,
                                        decay_paused=True,
                                    ),
                                ),
                            ),
                        )
                        world = WorldState(WorldSurface(800, 600), ())
                        memory = ObjectMemory()
                        progression = SessionTimeProgression(world, memory)
                        store = SqliteStateStore(
                            Path(d) / "fixture.sqlite3", definitions=()
                        )
                        revision = SaveRevision()
                        expected, wall = start, WALL
                        for duration in (0.016, 0.03, 29.999, 1e-10):
                            expected += duration
                            wall += duration
                            if with_world:
                                progression.advance(
                                    pet,
                                    SessionInputs(
                                        wall,
                                        0,
                                        False,
                                        None,
                                        False,
                                        False,
                                        None,
                                    ),
                                    duration,
                                )
                            else:
                                pet.advance(
                                    wall, elapsed_seconds=duration, observed=False
                                )
                            self.assertEqual(pet.lived_seconds, expected)
                            self.assertEqual(
                                bool(pet.wishes.active), expected < start + 0.04
                            )
                            validate_time_evidence(pet)
                            evidence = pet.moodlets.care_evidence
                            assert evidence is not None
                            self.assertTrue(
                                all(
                                    p.last_accounted_at == expected
                                    for p in evidence.progress
                                )
                            )
                            self.assertEqual(pet.sleeping, sleeping)
                            if sleeping:
                                self.assertAlmostEqual(
                                    pet.sleep_episode.slept_seconds,
                                    expected - start,
                                    places=9,
                                )
                                if expected - start > 5:
                                    recovering = next(
                                        p
                                        for p in pet.moodlets.active
                                        if p.definition_id
                                        == MoodletId.EXHAUSTION_IRRITATED
                                    )
                                    self.assertIsNotNone(recovering.recovery_since)
                            revision = store.save(
                                pet,
                                PetSettings(auto_routine=False),
                                expected_revision=revision,
                                adaptive=AdaptiveMemory(),
                                social_history=SocialContentHistory(),
                                world=world.snapshot() if with_world else None,
                                object_memory=memory.export(now=0)
                                if with_world
                                else None,
                            )
                            loaded = store.load_session()
                            self.assertEqual(
                                loaded.state.capture_checkpoint(),
                                pet.capture_checkpoint(),
                            )
                            restarted = PetSessionRestorer(
                                store,
                                wall_time=lambda: wall,
                            ).restore()
                            self.assertEqual(restarted.state.lived_seconds, expected)
                            self.assertEqual(restarted.state.moodlets, pet.moodlets)
                            self.assertEqual(restarted.revision, revision)

    def test_fractional_period_crossing_keeps_causes_and_cursors_on_one_axis(
        self,
    ) -> None:
        start = 86400 - 0.008
        moodlets = prepare_long_term(MoodletState(), elapsed=0)
        evidence = moodlets.care_evidence
        assert evidence is not None
        moodlets = replace(
            moodlets,
            care_evidence=replace(
                evidence,
                progress=tuple(
                    replace(
                        p,
                        last_accounted_at=start,
                        awake_contact_gap_seconds=start,
                        longest_awake_contact_gap_seconds=start,
                    )
                    for p in evidence.progress
                ),
            ),
        )
        pet = PetState(
            updated_at=WALL,
            lived_seconds=start,
            moodlets=moodlets,
            relationship=FriendshipHistory(baseline=0, continuous_since=0),
        )
        pet.advance(WALL + 0.016, elapsed_seconds=0.016, observed=False)
        validate_time_evidence(pet)
        episode = next(
            p for p in pet.moodlets.active if p.definition_id == MoodletId.OVERLOOKED
        )
        self.assertEqual(len(episode.causes), 1)
        self.assertEqual(episode.level, 1)
        period = episode.causes[0].period
        assert period is not None
        self.assertEqual(period.ended_at, 86400)
        evidence = pet.moodlets.care_evidence
        assert evidence is not None
        self.assertTrue(
            all(p.last_accounted_at == pet.lived_seconds for p in evidence.progress)
        )
        pet.advance(WALL + 0.032, elapsed_seconds=0.016, observed=False)
        validate_time_evidence(pet)
        later = next(
            p for p in pet.moodlets.active if p.definition_id == MoodletId.OVERLOOKED
        )
        self.assertEqual(later.causes, episode.causes)

    def test_live_clock_owns_duration_across_fractional_ticks_and_wall_correction(
        self,
    ) -> None:
        for with_world in (False, True):
            with self.subTest(with_world=with_world):
                pet = PetState(updated_at=WALL, lived_seconds=467390.5999761847)
                uptime, wall = [1234.5], WALL
                clock = ActiveSessionClock(lambda: uptime[0], wall_time=lambda: wall)
                progression = (
                    SessionTimeProgression(
                        WorldState(WorldSurface(800, 600), ()),
                        ObjectMemory(),
                    )
                    if with_world
                    else None
                )
                expected = pet.lived_seconds
                for duration in (0.016, 29.984, 0.03, 300.123456789):
                    previous = uptime[0]
                    uptime[0] += duration
                    expected += uptime[0] - previous
                    wall += duration
                    if duration == 0.03:
                        wall -= 3600  # Uptime continues despite corrected UTC.
                    inputs = SessionInputs(wall, 0, False, None, False, False, None)
                    advance_session_time(pet, clock, inputs, progression=progression)
                    self.assertEqual(pet.lived_seconds, expected)
                    validate_time_evidence(pet)
                    evidence = pet.moodlets.care_evidence
                    assert evidence is not None
                    self.assertTrue(
                        all(p.last_accounted_at == expected for p in evidence.progress)
                    )
                    checkpoint = pet.capture_checkpoint()
                    advance_session_time(pet, clock, inputs, progression=progression)
                    self.assertEqual(pet.capture_checkpoint(), checkpoint)

    def test_unmatched_step_or_final_endpoint_is_rejected_without_partial_rebase(
        self,
    ) -> None:
        pet = PetState(updated_at=WALL)
        checkpoint = pet.capture_checkpoint()
        plan = plan_pet_time(WALL, WALL + 1, elapsed_seconds=1, elapsed_start=1)
        assert plan is not None
        with self.assertRaises(ValueError):
            pet.advance_time_step(
                next(iter(plan)), auto_routine=False, sleep_context=SleepContext()
            )
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        with self.assertRaises(ValueError):
            pet.finish_time_advance(
                WALL + 1,
                lived_seconds=1,
                auto_routine=False,
                sleep_context=SleepContext(),
            )
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
