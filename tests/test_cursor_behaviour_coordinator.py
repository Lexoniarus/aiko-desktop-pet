"""Admission reads current activity without a second policy evaluation."""

import unittest
from dataclasses import replace

from aiko_pet.application.cursor_behaviour import (
    CursorActivityContext,
    CursorBehaviourCoordinator,
)
from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.application.settings import PetSettings
from aiko_pet.pet.interaction_events import CursorExperience, CursorWarningReceipt
from aiko_pet.pet.mind.cursor_attention import CursorAttention, CursorPerception
from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourPolicy
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class CursorCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.settings = PetSettings(auto_walk=True, follow_cursor=True)
        observer = CursorObservation(CursorAttention())
        observer.current = CursorPerception(
            10,
            (400, 194),
            0.6,
            speed=2,
            side=1,
            reachable=True,
            valid=True,
        )
        self.coordinator = CursorBehaviourCoordinator(
            PetState(), self.settings, observer, CursorBehaviourPolicy()
        )
        for n in range(65):
            observer.current = replace(observer.current, sampled_at=3.6 + n / 10)
            self.coordinator.begin_frame(3.6 + n / 10, CursorActivityContext())

    def test_real_activity_preserves_existing_moodlet_while_time_advances(self):
        co = self.coordinator
        before = co._state.moodlets.active[0]
        score = co.intent.attention
        for n in range(101, 121):
            co._state.advance(co._state.updated_at + .1, elapsed_seconds=.1)
            co._observer.current = replace(co._observer.current, sampled_at=n / 10)
            co.begin_frame(n / 10, CursorActivityContext(foreground_active=True))
            self.assertFalse(co.intent.moving)
            self.assertFalse(co.watching)
            self.assertIsNone(co.feedback)
        after = co._state.moodlets.active[0]
        self.assertEqual((after.instance_id, after.level),
                         (before.instance_id, before.level))
        self.assertAlmostEqual(after.remaining_seconds, before.remaining_seconds - 2)
        self.assertEqual(co.intent.attention, score)
        co._observer.current = replace(co._observer.current, sampled_at=12.1)
        co.begin_frame(12.1, CursorActivityContext())
        self.assertIsNone(co.feedback)
        self.assertEqual(co.intent.feeling, "curiosity")
        self.assertEqual(co._state.moodlets.active[0].instance_id, before.instance_id)

    def test_real_activity_does_not_revive_an_expired_moodlet(self):
        observer = CursorObservation(CursorAttention())
        co = CursorBehaviourCoordinator(
            PetState(), self.settings, observer, CursorBehaviourPolicy(),
        )
        at = 0.0
        for n in range(40):
            at = n / 10
            observer.current = CursorPerception(
                sampled_at=at, pointer=(500, 100), distance=1.5,
                speed=2, side=1, valid=True,
            )
            co.begin_frame(at, CursorActivityContext())
            if co.intent.experience is not None:
                break
        self.assertEqual(co.intent.feeling, "curiosity")
        self.assertIsNone(co._policy._known_feeling)
        for n in range(1, 411):
            co._state.advance(co._state.updated_at + .1, elapsed_seconds=.1)
            observer.current = replace(observer.current, sampled_at=at + n / 10)
            co.begin_frame(at + n / 10, CursorActivityContext(foreground_active=True))
            self.assertIsNone(co.feedback)
            self.assertFalse(co.intent.moving)
        self.assertFalse(co._state.moodlets.active)
        observer.current = replace(observer.current, sampled_at=at + 41.1)
        co.begin_frame(at + 41.1, CursorActivityContext())
        self.assertIsNone(co.intent.experience)
        self.assertIsNone(co.intent.feeling)
        self.assertFalse(co.intent.moving)

    def test_same_tick_world_change_denies_without_reselecting(self):
        intent = self.coordinator.intent
        self.assertTrue(intent.moving)
        self.assertIsNone(
            self.coordinator.admit_motion(
                CursorActivityContext(world_protected=True), 10
            )
        )
        self.assertIs(self.coordinator.intent, intent)
        self.assertIs(
            self.coordinator.admit_motion(CursorActivityContext(), 10), intent
        )

    def test_every_current_guard_and_stale_data_blocks(self):
        for key in [
            "game_open",
            "foreground_active",
            "world_protected",
        ]:
            self.assertIsNone(
                self.coordinator.admit_motion(
                    replace(CursorActivityContext(), **{key: True}), 10
                )
            )
        self.assertIsNone(self.coordinator.admit_motion(CursorActivityContext(), 11))
        self.settings.follow_cursor = False
        self.assertIsNone(self.coordinator.admit_motion(CursorActivityContext(), 10))

    def test_completion_is_delivered_once_and_pause_is_enforced(self):
        token = self.coordinator.intent.token
        self.coordinator.note_motion_finished(token, 10)
        self.coordinator.begin_frame(10.1, CursorActivityContext())
        self.assertFalse(self.coordinator.intent.moving)

    def test_qualified_event_commits_once_at_pet_endpoint(self):
        pet = self.coordinator._state
        self.assertEqual(len(pet.moodlets.active), 1)
        checkpoint = pet.capture_checkpoint()
        self.coordinator.begin_frame(10, CursorActivityContext())
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        self.coordinator.reset()
        self.assertEqual(pet.capture_checkpoint(), checkpoint)

    def test_sustained_play_escalates_refreshes_without_spam_and_then_expires(self):
        co = self.coordinator
        pet = co._state
        identity = pet.moodlets.active[0].instance_id
        feedback = []
        for n in range(101, 601):
            pet.advance(pet.updated_at + .1, elapsed_seconds=.1)
            co._observer.current = replace(
                co._observer.current, sampled_at=n / 10, speed=4,
                distance=1.5, reachable=False,
            )
            co.begin_frame(n / 10, CursorActivityContext())
            if co.feedback is not None:
                self.assertIsInstance(co.feedback, CursorExperience)
                assert isinstance(co.feedback, CursorExperience)
                feedback.append(co.feedback.level)
        current = pet.moodlets.active[0]
        self.assertEqual(current.instance_id, identity)
        self.assertEqual(current.level, 3)
        self.assertEqual(feedback, [2, 3])
        self.assertGreater(current.last_trigger_at, 40)
        triggered = current.last_trigger_at
        for n in range(601, 1701):
            pet.advance(pet.updated_at + .1, elapsed_seconds=.1)
            co._observer.current = replace(
                co._observer.current, sampled_at=n / 10, speed=0,
                stationary_seconds=2,
            )
            co.begin_frame(n / 10, CursorActivityContext())
            self.assertIsNone(co.feedback)
            if pet.moodlets.active:
                self.assertEqual(pet.moodlets.active[0].last_trigger_at, triggered)
        self.assertFalse(pet.moodlets.active)
        self.assertFalse(co.intent.gaze)
        self.assertFalse(co.intent.moving)

    def test_turning_reads_persisted_feeling_and_stops_using_it_after_expiry(self):
        self.coordinator.reset()
        observer = self.coordinator._observer
        for n in range(11):
            observer.current = replace(
                observer.current, sampled_at=20 + n / 10, speed=4, reachable=False,
            )
            self.coordinator.begin_frame(20 + n / 10, CursorActivityContext())
        self.assertEqual(self.coordinator.intent.feeling, "curiosity")
        self.assertEqual(self.coordinator.intent.side, 1)
        self.assertLess(self.coordinator.intent.attention, 45)
        observer.current = replace(observer.current, sampled_at=21.1, side=-1)
        self.coordinator.begin_frame(21.1, CursorActivityContext())
        self.assertEqual(self.coordinator.intent.side, -1)
        state = self.coordinator._state
        state.advance(state.updated_at + 100, elapsed_seconds=100)
        self.assertFalse(state.moodlets.active)
        observer.current = replace(observer.current, sampled_at=21.2, side=1)
        self.coordinator.begin_frame(21.2, CursorActivityContext())
        self.assertIsNone(self.coordinator.intent.feeling)
        self.assertNotEqual(self.coordinator.intent.side, 1)

    def test_real_fear_then_new_safe_interest_replace_each_other_once(self):
        co = self.coordinator
        old_receipt = co._state.moodlets.active[0].causes[-1].event_id
        co.note_motion_finished(co.intent.token, 10)

        def sample(at, closing=0, distance=.6):
            co._observer.current = replace(
                co._observer.current, sampled_at=at, speed=4,
                reachable=False, closing_speed=closing, distance=distance,
            )
            co.begin_frame(at, CursorActivityContext())

        for n in range(101, 221):
            sample(n / 10)
        set_test_pet_values(co._state, mood=20)
        sample(22.1, 2, .5)
        warning = co.intent.warning
        assert warning is not None
        co.note_warning(CursorWarningReceipt(warning.warning_id, 22.1, True))
        sample(22.2, -2, .5)
        sample(22.3, 2, .5)
        self.assertEqual(len(co._state.moodlets.active), 1)
        self.assertEqual(
            co._state.moodlets.active[0].definition_id.value, "cursor_fear",
        )
        co.note_motion_finished(co.intent.token, 22.4)
        feelings = []
        for n in range(225, 310):
            sample(n / 10)
            if co.intent.experience is not None:
                feelings.append(co.intent.experience.feeling)
        self.assertEqual(feelings, ["curiosity"])
        self.assertEqual(len(co._state.moodlets.active), 1)
        current = co._state.moodlets.active[0]
        self.assertEqual(current.definition_id.value, "cursor_curiosity")
        self.assertNotEqual(current.causes[-1].event_id, old_receipt)
