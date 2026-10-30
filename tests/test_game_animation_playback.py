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
