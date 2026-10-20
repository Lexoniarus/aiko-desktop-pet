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
from aiko_pet.desktop.visual_observation import DesktopVisualObservation
from aiko_pet.desktop.walk_runtime import WalkDriver
from aiko_pet.desktop.world_access import WorldRuntimeAccess
from aiko_pet.desktop.world_runtime import DesktopWorldRuntime
from aiko_pet.gui import DesktopPet
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
        world = MagicMock(spec=DesktopWorldRuntime)
        world.ready_for_handover.return_value = True
        access.bind(cast(DesktopWorldRuntime, world))
        self.assertTrue(access.ready_for_handover())
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
    def test_ready_hands_leave_cursor_custody_unchanged_until_release(self):
        try:
            probe = tk.Tk()
            probe.destroy()
        except tk.TclError as error:
            self.skipTest(str(error))
        directory = self.enterContext(tempfile.TemporaryDirectory())
        store = StateStore(Path(directory) / "state.json")
        store.save(PetState(satiety=76, energy=60), PetSettings(
            scale=2, auto_walk=False, auto_routine=False, observe_computer=False,
            learn_rhythm=False, spontaneous_talk=False,
        ))
        app = DesktopPet(store=store)
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
        image = world.view.image("energy_drink", 2)
        sprite = world.view.items.foods["energy_drink"].sprites[2]
        pointer = (int(eyes[0] + sprite.pivot[0] - image.width() / 2),
                   int(eyes[1] + sprite.pivot[1] - image.height() / 2))
        self.enterContext(patch.object(app.root, "winfo_pointerx",
                                      return_value=pointer[0]))
        self.enterContext(patch.object(app.root, "winfo_pointery",
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
            if world.ready_for_handover():
                break
        self.assertTrue(world.ready_for_handover())
        app._animated.render(time.monotonic(), pointer)
        self.assertEqual(app._animated.frame_clock.active_key, ("pick_up", 7))
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
        world.cursor.release()
        self.assertFalse(world.ready_for_handover())
        self.assertEqual(world.world.get(token).state, ObjectState.PET_HELD)
        self.assertEqual(world.interaction.phase, "handover")
