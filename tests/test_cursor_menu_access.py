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
from aiko_pet.pet.interaction_events import CursorExperience
from aiko_pet.pet.mind.cursor_attention import CursorAttention
from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourPolicy
from aiko_pet.pet.movement.contracts import MotionRequest
from aiko_pet.pet.state import PetState


class CursorMenuAccessTests(unittest.TestCase):
    def setUp(self):
        self.point = (110, 140)
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

    def test_self_contact_never_auto_claims_but_deliberate_motion_and_click_do(self):
        self.point = (200, 180)
        self.observer.attention.observe(self.point, 10.1)
        self.walk.last_placement_at = 11
        self.assertFalse(self.runtime.allow_hover())
        self.runtime.begin_behaviour(11)
        self.walk.clear_cursor_request.assert_not_called()
        self.point = (203, 180)
        self.runtime.begin_behaviour(11.1)
        self.walk.clear_cursor_request.assert_called_once()
        self.walk.clear_cursor_request.reset_mock()
        self.runtime.claim_access(self.point)
        self.walk.clear_cursor_request.assert_called_once()

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
        self.assertEqual(fixture.settings.x, 100)
        self.assertIs(driver.movement.request("world"), request)
        self.assertIsNone(driver.movement.request("cursor"))
        active[0] = False
        self.assertIsNotNone(
            driver.step(11, 0.5, game_mode=False, attention_active=False)
        )
        self.assertGreater(fixture.settings.x, 100)
