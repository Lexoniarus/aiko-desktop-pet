"""Forward gaze and empty-hand readiness preserve real interaction ownership."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.animation_runtime import (
    AnimationRuntimePorts,
    DesktopAnimationRuntime,
)
from aiko_pet.desktop.geometry import FOOT_BASELINE
from aiko_pet.desktop.visual_observation import (
    DesktopVisualObservation,
    VisualAttentionPorts,
)
from aiko_pet.desktop.walk_runtime import WalkDriver
from aiko_pet.desktop.world_access import WorldRuntimeAccess
from aiko_pet.desktop.world_runtime import DesktopWorldRuntime
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.pet.animation.animation import PassiveObservation, SpriteSelection
from aiko_pet.pet.animation.gaze import gaze_sector
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from aiko_pet.world.contracts import ObjectState
from tools.desktop_test_support import create_test_desktop
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import set_test_pet_values


class ForwardGazeTests(unittest.TestCase):
    def test_center_clears_every_previous_sector_at_both_scales(self) -> None:
        for scale in (1, 2):
            for previous in range(16):
                self.assertIsNone(gaze_sector(
                    -500, 100, -500 + 5 * scale, 100 + 5 * scale,
                    scale=scale, previous=previous,
                ))
            self.assertEqual(gaze_sector(0, 0, 17 * scale, 0, scale=scale), 4)

    def test_front_is_distinct_from_absent_attention_and_avoids_workload(self):
        settings = PetSettings()
        monitor = MagicMock()
        observer = DesktopVisualObservation(
            settings=settings, monitor=monitor, eyes=lambda: (100, 200),
        )
        for scale in (1, 2):
            settings.scale = scale
            observer.gaze_direction((1000, 200))
            result = observer.observe(1, (100, 200), 0, False)
            self.assertEqual(result, PassiveObservation(None, False, True))
            self.assertIsNone(observer.sector)
        monitor.latest.assert_not_called()
        self.assertFalse(observer.observe(10, (100, 200), 0, False).forward_gaze)
        self.assertFalse(observer.observe(11, (100, 200), 11, True).forward_gaze)
        settings.follow_cursor = False
        self.assertFalse(observer.observe(12, (100, 200), 12, False).forward_gaze)

    def test_item_center_adjusts_rendered_gaze_without_rewriting_sensor_target(self):
        observer = DesktopVisualObservation(
            settings=PetSettings(), monitor=MagicMock(), eyes=lambda: (100, 200),
            attention=VisualAttentionPorts(following_subject=lambda: "known_item"),
        )
        observer.object_target = (100, 230)
        before = observer.attention((100, 220), pointer_recent=True)
        rendered = observer.observe(1, (100, 220), 1, False,
                                    cursor_gaze_point=(100, 200))
        self.assertTrue(rendered.forward_gaze)
        self.assertEqual(observer.object_target, (100, 230))
        self.assertEqual(observer.attention((100, 220), pointer_recent=True), before)
        self.assertFalse(observer.observe(1, (100, 220), 1, True,
                                          cursor_gaze_point=(100, 200)).forward_gaze)


class CursorPoseRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState()
        self.walk = MagicMock(spec=WalkDriver)
        self.walk.movement = MagicMock()
        self.walk.movement.remaining_distance = 0
        self.walk.step.return_value = None
        self.visual = MagicMock(spec=DesktopVisualObservation)
        self.visual.observe.return_value = PassiveObservation(None, False, True)
        self.visual.orienting = False
        self.ready = False
        self.runtime = DesktopAnimationRuntime(
            state=self.state, settings=PetSettings(), assets=load_character_catalog(),
            walk=cast(WalkDriver, self.walk),
            visual=cast(DesktopVisualObservation, self.visual),
            ports=AnimationRuntimePorts(
                action_until=lambda: 0, action_clip_id=lambda: "review",
                attention_until=lambda: 0, ready_for_handover=lambda: self.ready,
            ),
        )

    def choose(self, *, game: bool = False, action: str | None = None):
        return self.runtime.select_animation(100, (100, 200), 100, game, action)

    def test_forward_look_preempts_ambient_glances_workload_and_low_needs(self):
        set_test_pet_values(self.state, energy=0, mood=0, satiety=0)
        self.runtime.ambient.next_glance_at = 0
        self.visual.observe.return_value = PassiveObservation(None, True, True)
        self.assertEqual(self.choose(),
                         RenderDecision(SpriteSelection("idle", 0), True))

    def test_only_ready_offer_selects_static_last_pickup_pose(self):
        self.ready = True
        self.assertEqual(self.choose(),
                         RenderDecision(SpriteSelection("pick_up", 7), True))
        self.ready = False
        self.assertEqual(self.choose(),
                         RenderDecision(SpriteSelection("idle", 0), True))

    def test_offer_does_not_preempt_sleep_game_active_action_or_walk(self):
        self.ready = True
        set_test_pet_values(self.state, sleeping=True)
        self.assertEqual(self.choose().sprite, SpriteSelection("sleep"))
        set_test_pet_values(self.state, sleeping=False)
        self.assertEqual(self.choose(game=True).sprite, SpriteSelection("waiting"))
        self.assertEqual(self.choose(action="eat").sprite, SpriteSelection("eat"))
        self.walk.step.return_value = "running-left"
        self.assertEqual(self.choose().sprite, SpriteSelection("running-left"))

    def test_late_world_port_reads_current_eligibility(self):
        access = WorldRuntimeAccess()
        self.assertFalse(access.ready_for_handover())
        self.assertIsNone(access.cursor_gaze_point())
        world = MagicMock(spec=DesktopWorldRuntime)
        world.ready_for_handover.return_value = True
        world.cursor_gaze_point.return_value = (100, 200)
        access.bind(cast(DesktopWorldRuntime, world))
        self.assertTrue(access.ready_for_handover())
        self.assertEqual(access.cursor_gaze_point(), (100, 200))
        world.ready_for_handover.return_value = False
        self.assertFalse(access.ready_for_handover())


class EmptyHandPreviewTests(unittest.TestCase):
    def test_preview_emits_no_pickup_events_and_shows_no_stale_food(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.addCleanup(root.destroy)
        root.withdraw()
        canvas = tk.Canvas(root)
        settings = PetSettings()
        decision = RenderDecision(SpriteSelection("pick_up", 7), True)
        pet = AnimatedPet(
            root, canvas, PetState(), settings,
            AnimatedPorts(
                walk_step=lambda _now, _elapsed: None,
                walk_active=lambda: False, interrupt_walk=lambda: None,
                choose_animation=lambda *_args: decision, reset_gaze=lambda: None,
                extend_action=lambda _deadline: None,
            ), assets=load_character_catalog(), items=load_item_catalog(),
            ambient=AmbientDirector(started_at=time.monotonic()),
        )
        self.addCleanup(pet.close)
        playback = MagicMock()
        pet.on_playback = playback
        for scale in (1, 2):
            settings.scale = scale
            pet.reload_sprites()
            pet.food_overlay.select("onigiri")
            pet.render(time.monotonic(), (96 * scale, 82 * scale))
            self.assertEqual(pet.frame_clock.active_key, ("pick_up", 7))
            self.assertEqual(canvas.itemcget(pet.food_overlay.item, "state"),
                             "hidden")
            self.assertIsNone(pet.food_overlay.current_food_id)
        playback.assert_not_called()


class HandoverPreviewIntegrationTests(unittest.TestCase):
    def test_face_hand_and_side_positions_at_native_scale(self):
        self.exercise_offer_positions(1)

    def test_face_hand_and_side_positions_at_double_scale(self):
        self.exercise_offer_positions(2)

    def exercise_offer_positions(self, scale):
        try:
            probe = tk.Tk()
            probe.destroy()
        except tk.TclError as error:
            self.skipTest(str(error))
        directory = self.enterContext(tempfile.TemporaryDirectory())
        store = StateStore(Path(directory) / "state.json")
        save_test_session(store, PetState(satiety=76, energy=60), PetSettings(
            scale=scale, auto_walk=False, auto_routine=False, observe_computer=False,
            learn_rhythm=False, spontaneous_talk=False,
        ))
        app = create_test_desktop(store=store)
        self.addCleanup(app.quit)
        app._runtime.stop()
        greeting = app._runtime.scheduled_greeting
        if greeting is not None:
            app.root.after_cancel(greeting)
            app._runtime.scheduled_greeting = None
        world = app._world
        assert world._timer is not None
        app.root.after_cancel(world._timer)
        world._timer = None
        app.root.update_idletasks()
        eyes = app._animated.cursor_eye_position
        image = world.view.image("energy_drink", scale)
        sprite = world.view.items.foods["energy_drink"].sprites[scale]
        pointer = (int(eyes[0] + sprite.pivot[0] - image.width() / 2),
                   int(eyes[1] + sprite.pivot[1] - image.height() / 2))
        pointer_x = self.enterContext(patch.object(app.root, "winfo_pointerx",
                                                 return_value=pointer[0]))
        pointer_y = self.enterContext(patch.object(app.root, "winfo_pointery",
                                                 return_value=pointer[1]))
        self.enterContext(patch(
            "aiko_pet.desktop.cursor_item_gesture.mouse_buttons_down_windows",
            return_value=(True, False),
        ))
        self.assertFalse(world.ready_for_handover())
        world.begin_carry("energy_drink")
        token = world.cursor.instance_id
        assert token is not None
        self.assertFalse(world.ready_for_handover())  # No instant identification.
        for _ in range(120):
            # Exercise perception and receipt ordering without gameplay waits.
            world.now += .05
            world.update(time.monotonic())
            player = app._reaction_player
            if player.pending_timer is not None:
                app.root.after_cancel(player.pending_timer)
                player._complete(player.generation)
            if world.cursor.offer_ready and world._can_acquire(token):
                break
        self.assertTrue(world.cursor.offer_ready)
        self.assertTrue(world._can_acquire(token))

        def render_at(center):
            pointer = (int(center[0] + sprite.pivot[0] - image.width() / 2),
                       int(center[1] + sprite.pivot[1] - image.height() / 2))
            pointer_x.return_value, pointer_y.return_value = pointer
            world.cursor.update()
            world.now += .05
            world.update(time.monotonic())
            app._animated.render(time.monotonic(), pointer)
            self.assertEqual(world.world.get(token).state, ObjectState.USER_HELD)
            return app._animated.frame_clock.active_key

        self.assertEqual(render_at(eyes), ("idle", 0))
        self.assertFalse(world.ready_for_handover())
        clip = app._animated.assets.clips["pick_up"]
        hand_anchor = clip.frames[-1].food_anchor
        assert hand_anchor is not None
        hands = ((app.settings.x or 0) + (96 - clip.anchor[0]
                                         + hand_anchor[0]) * scale,
                 (app.settings.y or 0) + (FOOT_BASELINE - clip.anchor[1]
                                         + hand_anchor[1]) * scale)
        self.assertEqual(render_at(hands), ("pick_up", 7))
        self.assertTrue(world.ready_for_handover())
        self.assertEqual(render_at((eyes[0], eyes[1] + 12 * scale)), ("idle", 0))
        self.assertFalse(world.ready_for_handover())
        self.assertEqual(render_at((eyes[0] + 80 * scale, eyes[1])), ("look", 4))
        self.assertFalse(world.ready_for_handover())
        self.assertEqual(render_at((hands[0] + 23 * scale, hands[1])),
                         ("pick_up", 7))
        self.assertNotEqual(render_at((hands[0] + 25 * scale, hands[1])),
                            ("pick_up", 7))
        self.assertEqual(render_at(hands), ("pick_up", 7))
        self.assertEqual(world.world.get(token).state, ObjectState.USER_HELD)
        self.assertEqual(world.interaction.phase, "idle")
        self.assertLess(app.state.energy, 61)
        self.assertEqual(app.canvas.itemcget(app._animated.food_overlay.item, "state"),
                         "hidden")
        world.cursor.inside = False
        self.assertFalse(world.ready_for_handover())
        world.cursor.inside = True
        set_test_pet_values(app.state, energy=100)
        self.assertFalse(world.ready_for_handover())  # A live refusal hides hands.
        set_test_pet_values(app.state, energy=60)
        # Face-level release keeps the established handover rules as well.
        self.assertEqual(render_at(eyes), ("idle", 0))
        world.cursor.release()
        self.assertFalse(world.ready_for_handover())
        self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
        self.assertEqual(world.interaction.phase, "handover")
