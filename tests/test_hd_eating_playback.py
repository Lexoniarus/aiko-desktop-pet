"""Play a complete isolated HD meal through native Tk and the real frame clock."""

import tkinter as tk
import unittest
from dataclasses import replace

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.pet.animation.animation import SpriteSelection
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.action_playback import ActionPlayback
from aiko_pet.ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from tools.tk_test_time import ControlledTkTime


class HdEatingPlaybackTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.canvas = tk.Canvas(self.root, width=384, height=416)
        self.settings = PetSettings(x=0, y=0, scale=2)
        self.state = PetState()
        self.assets = load_character_catalog()
        self.anim = AnimatedPet(
            self.root, self.canvas, self.state, self.settings,
            AnimatedPorts(
                walk_step=lambda *_args: None, walk_active=lambda: False,
                interrupt_walk=lambda: None,
                choose_animation=lambda *_args: RenderDecision(SpriteSelection("idle")),
                reset_gaze=lambda: None, extend_action=lambda _deadline: None,
            ), assets=self.assets, items=load_item_catalog(),
            ambient=AmbientDirector(started_at=0),
        )
        self.addCleanup(self.anim.close)

    def test_three_timed_bites_complete_once_without_mutating_pet_state(self):
        clip = self.assets.clip_for("eat", 2)
        self.assertIn("eat", self.assets.hd_action_clips)
        before = self.state.capture_checkpoint()
        events = []
        self.anim.on_playback = events.append
        action = ActionPlayback(self.assets, begin=self.anim.begin_action,
                                cancel=self.anim.cancel_action)
        self.anim.ports = replace(self.anim.ports, extend_action=action.extend)
        with ControlledTkTime() as clock:
            self.anim.set_food_overlay("onigiri")
            action.start("eat", 0, started_at=clock.monotonic())
            self.assertAlmostEqual(action.until - clock.monotonic(),
                                   clip.duration_seconds)
            clock.advance(clip.duration_seconds + .05)
        played = [e for e in events if not e.finished and e.clip_id == "eat"]
        self.assertEqual([e.source_index for e in played],
                         list(range(len(clip.frames))))
        self.assertEqual(sum(e.events == ("bite",) for e in played), 3)
        self.assertEqual(sum(e.finished for e in events), 1)
        self.assertEqual(self.anim._display_clip, "idle")
        self.assertEqual(self.canvas.itemcget(self.anim.food_overlay.item, "state"),
                         "hidden")
        self.assertEqual(self.state.capture_checkpoint(), before)

    def test_food_stays_until_last_bite_and_world_refresh_cannot_restore_it(self):
        clip = self.assets.clip_for("eat", 2)
        self.anim.set_food_overlay("sandwich")
        bites = 0
        for index, frame in enumerate(clip.frames):
            bites += frame.events.count("bite")
            self.anim.show_frame("eat", index, fixed=index)
            self.anim.refresh_food_overlay()
            expected = "hidden" if bites == 3 else "normal"
            self.assertEqual(self.canvas.itemcget(self.anim.food_overlay.item, "state"),
                             expected, index)
        self.assertEqual(bites, 3)

    def test_scale_switch_uses_matching_clip_images_and_can_cancel(self):
        self.anim.set_food_overlay("onigiri")
        self.anim.begin_action("eat", 0)
        self.anim.show_frame("eat", .1,
                             fixed=len(self.assets.clip_for("eat", 2).frames) - 5)
        for scale in (1, 2):
            self.settings.scale = scale
            self.anim.reload_sprites()
            clip = self.assets.clip_for("eat", scale)
            self.assertEqual(len(self.anim.sprites["eat"]), len(clip.frames))
            self.assertEqual(self.anim.sprites["eat"][0].width(), 192 * scale)
        self.anim.cancel_action(1)
        self.assertEqual(self.anim._display_clip, "idle")
        self.assertEqual(self.canvas.itemcget(self.anim.food_overlay.item, "state"),
                         "hidden")
