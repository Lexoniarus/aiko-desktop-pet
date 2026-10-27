"""Admission reads current activity without a second policy evaluation."""

import unittest
from dataclasses import replace

from aiko_pet.application.cursor_behaviour import (
    CursorActivityContext,
    CursorBehaviourCoordinator,
)
from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.application.settings import PetSettings
from aiko_pet.pet.mind.cursor_attention import CursorAttention, CursorPerception
from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourPolicy
from aiko_pet.pet.state import PetState


class CursorCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.settings = PetSettings(auto_walk=True, follow_cursor=True)
        observer = CursorObservation(CursorAttention())
        observer.current = CursorPerception(
            10,
            (400, 194),
            0.6,
            stationary_seconds=4,
            side=1,
            reachable=True,
            valid=True,
        )
        self.coordinator = CursorBehaviourCoordinator(
            PetState(), self.settings, observer, CursorBehaviourPolicy()
        )
        for n in range(47):
            observer.current = replace(observer.current, sampled_at=5.4 + n / 10)
            self.coordinator.begin_frame(5.4 + n / 10, CursorActivityContext())

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
            "menu_engaged",
            "foreground_active",
            "world_protected",
            "direct_contact",
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
