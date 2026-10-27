"""Native input access immediately wins without deleting World work."""

import unittest
from dataclasses import replace
from unittest.mock import Mock

import test_desktop_walk_runtime as walk_fixtures

from aiko_pet.application.cursor_behaviour import CursorBehaviourCoordinator
from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.geometry import sprite_access_contains
from aiko_pet.desktop.pointer_runtime import PointerRuntime, PointerRuntimePorts
from aiko_pet.pet.interaction_events import CursorExperience, CursorWarningReceipt
from aiko_pet.pet.mind.cursor_attention import CursorAttention, CursorPerception
from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourPolicy
from aiko_pet.pet.movement.contracts import MotionRequest
from aiko_pet.pet.state import PetState


class CursorMenuAccessTests(unittest.TestCase):
    def setUp(self):
        self.point: tuple[int, int] = (110, 140)
        self.menu = False
        self.observer = CursorObservation(CursorAttention())
        self.observer.attention.observe(self.point, 10)
        self.pet = PetState()
        self.coordinator = CursorBehaviourCoordinator(
            self.pet,
            PetSettings(),
            self.observer,
            CursorBehaviourPolicy(session_id="access"),
        )
        self.walk = Mock()
        self.walk.last_placement_at = 9
        self.runtime = PointerRuntime(
            self.observer,
            PointerRuntimePorts(
                sample=lambda: (*self.point, 1000),
                game_mode=lambda: False,
                eyes=lambda: (196, 182),
                on_motion=Mock(),
                sprite_origin=lambda: (100, 100),
                menu_engaged=lambda: self.menu,
            ),
            self.coordinator,
            self.walk,
        )

    def test_one_geometry_margin_at_both_scales(self):
        for scale in (1, 2):
            self.assertTrue(
                sprite_access_contains(
                    (100 + 45 * scale, 100 + 32 * scale), (100, 100), scale
                )
            )
            self.assertFalse(
                sprite_access_contains(
                    (100 + 44 * scale, 100 + 31 * scale), (100, 100), scale
                )
            )

    def test_fast_native_contact_before_sensor_tick_claims_and_releases_now(self):
        self.point = (200, 180)
        self.assertTrue(self.runtime.control_active())
        self.walk.clear_cursor_request.assert_not_called()  # permission reads are pure
        self.runtime.claim_access(self.point)
        self.walk.clear_cursor_request.assert_called_once()
        self.assertFalse(self.coordinator.intent.moving)

    def test_motion_admits_hover_but_only_explicit_click_claims_access(self):
        self.point = (200, 180)
        self.observer.attention.observe(self.point, 10.1)
        self.walk.last_placement_at = 11
        self.assertFalse(self.runtime.allow_hover())
        self.runtime.begin_behaviour(11)
        self.walk.clear_cursor_request.assert_not_called()
        self.point = (203, 180)
        self.runtime.begin_behaviour(11.1)
        self.assertTrue(self.runtime.allow_hover())
        self.walk.clear_cursor_request.assert_not_called()
        self.runtime.claim_access(self.point)
        self.walk.clear_cursor_request.assert_called_once()

    def attend(self):
        self.point = (800, 100)
        for n in range(61):
            self.observer.current = CursorPerception(
                sampled_at=10 + n / 10, pointer=self.point, distance=1.5,
                speed=4, side=1, valid=True,
            )
            self.runtime.begin_behaviour(10 + n / 10)

    def test_flyover_keeps_attention_moodlet_and_body_after_leaving(self):
        self.attend()
        before = self.pet.capture_checkpoint()
        self.point = (200, 180)
        self.observer.current = replace(
            self.observer.current, sampled_at=16.1, pointer=self.point,
        )
        self.runtime.begin_behaviour(16.1)
        self.assertFalse(self.runtime.control_active())
        self.assertTrue(self.coordinator.watching)
        self.assertEqual(self.coordinator.intent.attention, 100)
        self.assertEqual(self.coordinator.intent.body, "profile")
        self.assertFalse(self.coordinator._policy._access)
        self.assertEqual(self.pet.capture_checkpoint(), before)
        self.walk.clear_cursor_request.assert_not_called()
        self.point = (800, 100)
        self.observer.current = replace(
            self.observer.current, sampled_at=16.2, pointer=self.point,
        )
        self.runtime.begin_behaviour(16.2)
        self.assertEqual(self.coordinator.intent.body, "profile")
        self.assertFalse(self.coordinator._policy._access)

    def test_menu_pauses_motion_without_resetting_attention_or_latching_access(self):
        self.attend()
        self.menu = True
        self.observer.current = replace(self.observer.current, sampled_at=16.1)
        self.runtime.begin_behaviour(16.1)
        self.assertTrue(self.runtime.control_active())
        self.assertTrue(self.coordinator.watching)
        self.assertEqual(self.coordinator.intent.attention, 100)
        self.assertFalse(self.coordinator._policy._access)
        self.assertFalse(self.runtime.motion_allowed())
        self.menu = False
        self.observer.current = replace(self.observer.current, sampled_at=16.2)
        self.runtime.begin_behaviour(16.2)
        self.assertTrue(self.coordinator.watching)
        self.assertEqual(self.coordinator.intent.body, "front")

    def test_flyover_does_not_cancel_a_still_valid_catching_attempt(self):
        self.attend()
        self.observer.current = replace(
            self.observer.current, sampled_at=16.1, distance=.6, reachable=True,
        )
        self.runtime.begin_behaviour(16.1)
        first = self.coordinator.intent
        self.assertTrue(first.moving)
        self.point = (200, 180)
        self.observer.current = replace(
            self.observer.current, sampled_at=16.2, pointer=self.point,
        )
        self.runtime.begin_behaviour(16.2)
        self.runtime.admit_behaviour(16.2)
        self.assertEqual(self.coordinator.intent.token, first.token)
        self.assertTrue(self.coordinator.intent.moving)
        self.assertEqual(self.coordinator.intent.target, self.point)
        self.walk.apply_cursor_intent.assert_called_once_with(
            self.coordinator.intent, 16.2,
        )
        self.walk.clear_cursor_request.assert_not_called()

    def test_control_use_cannot_turn_an_old_warning_into_new_fear(self):
        self.attend()
        self.runtime._ports = replace(
            self.runtime._ports, on_warning=lambda event, now: CursorWarningReceipt(
                event.warning_id, now, True,
            ),
        )
        self.observer.current = replace(
            self.observer.current, sampled_at=16.1, distance=.5, closing_speed=2,
        )
        self.runtime.begin_behaviour(16.1)
        self.assertEqual(self.coordinator._policy._warned_at, 16.1)
        before = self.pet.capture_checkpoint()
        self.menu = True
        for at, closing in ((16.2, -2), (16.3, 2)):
            self.observer.current = replace(
                self.observer.current, sampled_at=at, closing_speed=closing,
            )
            self.runtime.begin_behaviour(at)
        self.assertTrue(self.coordinator.watching)
        self.assertEqual(self.coordinator.intent.attention, 100)
        self.assertIsNone(self.coordinator._policy._warned_at)
        self.assertEqual(self.pet.capture_checkpoint(), before)
        self.menu = False
        self.observer.current = replace(self.observer.current, sampled_at=16.4)
        self.runtime.begin_behaviour(16.4)
        self.assertEqual(self.pet.capture_checkpoint(), before)

    def test_lingering_fear_does_not_override_contact_or_restart_escape(self):
        self.pet.experience_cursor(CursorExperience("earlier", "fear", 3))
        self.point = (200, 180)
        self.runtime.claim_access(self.point)
        self.runtime.begin_behaviour(12)
        self.assertFalse(self.coordinator.intent.moving)
        self.assertEqual(len(self.pet.moodlets.active), 1)
        self.menu = True
        self.point = (800, 800)
        self.assertTrue(self.runtime.control_active())
        self.menu = False
        self.assertFalse(self.runtime.control_active())

    def test_hard_access_pauses_committed_world_request_then_resumes(self):
        fixture = walk_fixtures.WalkDriverTests()
        fixture.setUp()
        driver = fixture.driver
        active = [True]
        driver.ports = replace(
            driver.ports, committed_goal=lambda: True, hard_access=lambda: active[0]
        )
        driver.set_world_goal(150)
        request = driver.movement.request("world")
        driver.submit_cursor_intent(MotionRequest("cursor", 7, 116, "step", 100))
        self.assertIsNone(driver.step(10, 0.5, game_mode=False, attention_active=False))
        self.assertEqual(fixture.settings.x or 0, 100)
        self.assertIs(driver.movement.request("world"), request)
        self.assertIsNone(driver.movement.request("cursor"))
        active[0] = False
        self.assertIsNotNone(
            driver.step(11, 0.5, game_mode=False, attention_active=False)
        )
        self.assertGreater(fixture.settings.x or 0, 100)

    def test_access_clears_attention_and_warning_but_preserves_moodlet(self):
        policy = self.coordinator._policy
        from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourContext

        context = CursorBehaviourContext(1, 80, 50)
        for n in range(40):
            policy.evaluate(CursorPerception(
                sampled_at=10 + n / 10, distance=1.5, speed=4, side=1, valid=True,
            ), context, 10 + n / 10)
        self.assertEqual(policy.stage, 3)
        warning = policy.evaluate(CursorPerception(
            sampled_at=14, distance=.5, speed=4, closing_speed=2,
            side=1, valid=True,
        ), context, 14).warning
        assert warning is not None
        self.pet.experience_cursor(CursorExperience("retained", "curiosity", 2))
        before = self.pet.capture_checkpoint()
        self.runtime.claim_access((200, 180))
        policy.note_warning(CursorWarningReceipt(warning.warning_id, 14.1, True))
        self.assertEqual((policy.attention, policy.stage), (0, 0))
        self.assertIsNone(policy._warned_at)
        self.assertEqual(self.pet.capture_checkpoint(), before)
        self.walk.clear_cursor_request.assert_called_once()

    def test_sleep_and_cursor_off_invalidate_sensor_history_at_owner_boundary(self):
        from tools.pet_test_support import set_test_pet_values

        for sleeping in (True, False):
            set_test_pet_values(self.pet, sleeping=False)
            self.coordinator._settings.follow_cursor = True
            self.coordinator.begin_frame(9, self.runtime.activity())
            self.observer.attention.observe((300, 100), 10)
            self.observer.attention.observe((400, 100), 10.1)
            set_test_pet_values(self.pet, sleeping=sleeping)
            self.coordinator._settings.follow_cursor = sleeping
            self.coordinator.begin_frame(10.1, self.runtime.activity())
            self.assertIsNone(self.observer.attention.previous_pointer)
            self.assertFalse(self.observer.current.valid)

    def test_cursor_off_keeps_contact_origin_after_the_transition_reset(self):
        self.coordinator._settings.follow_cursor = False
        self.coordinator.begin_frame(10, self.runtime.activity())
        self.point = (200, 180)
        self.observer.attention.observe(self.point, 10.1)
        self.observer.attention.observe(self.point, 10.2)
        self.walk.last_placement_at = 11
        self.coordinator.begin_frame(11, self.runtime.activity())
        self.assertEqual(self.observer.attention.previous_pointer, self.point)
        self.assertFalse(self.runtime.allow_hover())
        self.point = (204, 180)
        self.assertTrue(self.runtime.allow_hover())
        self.assertFalse(self.coordinator.watching)

    def test_mode_reset_invalidates_sample_and_preserves_persisted_impression(self):
        self.pet.experience_cursor(CursorExperience("existing", "fear", 2))
        before = self.pet.capture_checkpoint()
        self.observer.observe((100, 100), 10, game_mode=False,
                              eyes=(196, 182), screen_width=1000)
        self.observer.observe((110, 100), 10.14, game_mode=False,
                              eyes=(196, 182), screen_width=1000)
        self.assertTrue(self.observer.current.valid)
        self.runtime.reset()
        self.assertFalse(self.observer.current.valid)
        self.assertIsNone(self.observer.attention.previous_pointer)
        self.assertEqual(self.pet.capture_checkpoint(), before)
        self.walk.set_world_goal.assert_not_called()
