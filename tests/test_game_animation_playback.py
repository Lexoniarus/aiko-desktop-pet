"""Game markers use the sprite clock and cannot revive cancelled actions."""

import tkinter as tk
import unittest

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.pet.animation.animation import SpriteSelection
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from tools.tk_test_time import ControlledTkTime


class GameAnimationPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.clock = self.enterContext(ControlledTkTime())
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.state = PetState()
        self.settings = PetSettings(x=100, y=200)
        self.anim = AnimatedPet(
            self.root, tk.Canvas(self.root), self.state, self.settings,
            AnimatedPorts(
                walk_step=lambda *_: None, walk_active=lambda: False,
                interrupt_walk=lambda: None,
                choose_animation=lambda *_: RenderDecision(SpriteSelection("idle")),
                reset_gaze=lambda: None, extend_action=lambda _: None,
            ), assets=load_character_catalog(), items=load_item_catalog(),
            ambient=AmbientDirector(started_at=self.clock.monotonic()),
        )
        self.addCleanup(self.anim.close)
        self.anim.set_game_mode(True)

    def test_game_entry_clears_a_previous_care_graphic_without_changing_care(self):
        food_id = next(iter(self.anim.food_overlay._foods))
        self.anim.set_food_overlay(food_id)
        before = self.state.capture_checkpoint()
        self.anim.set_game_mode(True)
        self.assertIsNone(self.anim.food_overlay.current_food_id)
        self.assertEqual(self.state.capture_checkpoint(), before)

    def test_all_poses_and_midpoint_are_reported_from_the_actual_clock(self):
        before = self.state.capture_checkpoint()
        frames, done, world = [], [], []
        self.anim.on_playback = world.append
        start = self.clock.monotonic()
        self.anim.play_game_action(
            "attack", 900,
            lambda index: frames.append((index, self.clock.monotonic() - start)),
            lambda: done.append(True),
        )
        self.clock.advance(.451)
        self.assertEqual([i for i, _ in frames], [0, 1, 2, 3, 4])
        self.assertAlmostEqual(frames[-1][1], .450, places=3)
        self.clock.advance(.450)
        self.assertEqual([i for i, _ in frames], list(range(8)))
        self.assertEqual(done, [True])
        self.assertEqual(world, [])
        self.assertEqual(self.state.capture_checkpoint(), before)
        self.assertEqual((self.settings.x, self.settings.y), (100, 200))

    def test_cancel_drops_the_old_callback_even_if_already_queued(self):
        frames, done = [], []
        self.anim.play_game_action("attack", 900, frames.append,
                                   lambda: done.append(True))
        generation = self.anim._frame_generation
        self.anim.cancel_game_action()
        self.anim._advance_frame("attack", None, generation)
        self.clock.advance(2)
        self.assertEqual(frames, [0])
        self.assertEqual(done, [])

    def test_next_cycle_is_not_overwritten_by_the_completed_action(self):
        frames, done = [], []

        def again():
            self.anim.play_game_action("attack", 900, frames.append,
                                       lambda: done.append(True))

        self.anim.play_game_action("attack", 900, frames.append, again)
        self.clock.advance(1.81)
        self.assertEqual(frames, list(range(8)) * 2)
        self.assertEqual(done, [True])

    def test_authored_meal_plays_all_phases_at_both_sizes_without_care_effects(self):
        before = self.state.capture_checkpoint()
        for scale in (1, 2):
            with self.subTest(scale=scale):
                self.settings.scale = scale
                self.anim.reload_sprites()
                clip = self.anim.assets.clip_for("eat", scale)
                frames, done = [], []
                self.anim.play_game_action("eat", None, frames.append,
                                           lambda: done.append(True))
                self.clock.advance(clip.duration_seconds - .01)
                self.assertEqual(done, [])
                self.clock.advance(.02)
                self.assertEqual(frames, list(range(85)))
                self.assertEqual([i for i in frames if clip.frames[i].events],
                                 [18, 42, 66])
                self.assertEqual(done, [True])
        self.assertEqual(self.state.capture_checkpoint(), before)

    def test_obsolete_eight_frame_meal_timing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "all authored frames"):
            self.anim.play_game_action("eat", (400,) * 8, lambda _: None,
                                       lambda: None)

    def test_size_switch_keeps_authored_meal_progress_and_single_completion(self):
        frames, done = [], []
        self.anim.play_game_action("eat", None, frames.append,
                                   lambda: done.append(True))
        self.clock.advance(1.5)
        index = self.anim.frame_clock.frame_index
        self.settings.scale = 2
        self.anim.reload_sprites()
        self.assertEqual(self.anim.frame_clock.frame_index, index)
        self.clock.advance(7.42 - 1.5 + .01)
        self.assertEqual(frames, list(range(85)))
        self.assertEqual(done, [True])
