"""Native item rendering without game state, physical custody or menu wiring."""

import time
import tkinter as tk
import unittest

from aiko_pet.application.settings import PetSettings
from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.desktop.geometry import FOOT_BASELINE
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.pet.animation.animation import SpriteSelection
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from aiko_pet.ui.view_models.food_models import food_choices
from aiko_pet.ui.world_view import WorldView


class FoodRenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.canvas = tk.Canvas(self.root, width=192, height=208)
        self.settings = PetSettings(x=0, y=0)
        self.items = load_item_catalog()
        self.anim = AnimatedPet(
            self.root, self.canvas, PetState(), self.settings,
            AnimatedPorts(
                walk_step=lambda _now, _elapsed: None,
                walk_active=lambda: False,
                interrupt_walk=lambda: None,
                choose_animation=lambda *_args: RenderDecision(SpriteSelection("idle")),
                reset_gaze=lambda: None,
                extend_action=lambda _deadline: None,
            ),
            assets=load_character_catalog(), items=self.items,
            ambient=AmbientDirector(started_at=time.monotonic()),
        )
        self.addCleanup(self.anim.close)
        self.view = WorldView(self.root, self.items)
        self.addCleanup(self.view.close)

    def test_closed_book_visible_center_matches_open_book_at_both_scales(self):
        overlay = self.anim.food_overlay
        overlay.select("horoscope_book")
        book = self.items.readables["horoscope_book"]
        for scale in (1, 2):
            centers = {}
            for state in ("carry_closed", "half_open", "open_reading"):
                image = overlay._book_images[("horoscope_book", state, scale)]
                columns = [x for x in range(image.width())
                           if any(not image.transparency_get(x, y)
                                  for y in range(image.height()))]
                centers[state] = (min(columns) + max(columns) + 1) / 2
            for name in ("pick_up", "put_down"):
                clip = self.anim.assets.clips[name]
                for frame in clip.frames:
                    if frame.food_anchor is None:
                        continue
                    visible_centers = {}
                    for state in centers:
                        overlay.readable_state = state
                        overlay.render(clip, frame, scale=scale)
                        left, top = self.canvas.coords(overlay.item)
                        visible_centers[state] = left + centers[state]
                        if state != "carry_closed":
                            sprite = book.states[state][scale]
                            x = (96 - clip.anchor[0] + frame.food_anchor[0]) * scale
                            y = (FOOT_BASELINE - clip.anchor[1]
                                 + frame.food_anchor[1] + 12) * scale
                            self.assertEqual((left, top), (
                                round(x - sprite.pivot[0]),
                                round(y - sprite.pivot[1]),
                            ))
                    self.assertAlmostEqual(visible_centers["carry_closed"],
                                           visible_centers["open_reading"], delta=1)

    def test_png_assets_are_64_pixels_and_have_alpha(self) -> None:
        choices = food_choices(self.items)
        self.assertEqual(len(choices), 11)
        for choice in choices:
            with self.subTest(food=choice.id):
                self.assertEqual(
                    choice.image_path.parent,
                    ASSET_ROOT / "items" / "icons" / "64",
                )
                self.assertTrue(choice.image_path.is_file())
                image = tk.PhotoImage(
                    master=self.root, file=str(choice.image_path),
                )
                self.assertEqual((image.width(), image.height()), (64, 64))
                self.assertTrue(image.transparency_get(0, 0))

    def test_all_native_food_overlays_render_at_both_scales(self) -> None:
        overlay = self.anim.food_overlay
        for scale in (1, 2):
            self.settings.scale = scale
            self.canvas.configure(width=192 * scale, height=208 * scale)
            self.anim.reload_sprites()
            for choice in food_choices(self.items):
                with self.subTest(scale=scale, food=choice.id):
                    self.anim.set_food_overlay(choice.id)
                    self.anim.begin_action("eat", time.monotonic())
                    self.assertEqual(
                        self.canvas.itemcget(overlay.item, "state"),
                        "normal",
                    )
                    expected = overlay._images[(choice.id, scale)]
                    sprite = self.items.foods[choice.id].sprites[scale]
                    self.assertEqual(expected.cget("file"), str(sprite.render_path))
                    self.assertEqual(
                        self.view.image(choice.id, scale).cget("file"),
                        str(sprite.render_path),
                    )
                    actual = self.canvas.itemcget(overlay.item, "image")
                    self.assertEqual(actual, str(expected))
                    self.anim.show_frame(
                        "idle", time.monotonic(), fixed=0,
                    )
                    self.assertEqual(
                        self.canvas.itemcget(overlay.item, "state"),
                        "hidden",
                    )

    def test_switching_scale_does_not_interrupt_animation_timers(self) -> None:
        self.anim.set_food_overlay("cupcake")
        self.anim.begin_action("eat", time.monotonic())
        clock = self.anim.frame_clock
        for scale in (2, 1, 2):
            self.settings.scale = scale
            self.canvas.configure(width=192 * scale, height=208 * scale)
            self.anim.reload_sprites()
            self.assertIs(self.anim.frame_clock, clock)
            self.assertEqual(
                self.anim.food_overlay.current_food_id, "cupcake",
            )
            self.assertIsNotNone(self.anim._frame_timer)

    def test_hand_overlay_uses_the_eight_authored_frame_anchors(self) -> None:
        animated = self.anim
        clip = animated.assets.clips["eat"]
        self.assertEqual(len(clip.frames), 8)
        self.assertTrue(all(frame.food_anchor is not None for frame in clip.frames))
        animated.set_food_overlay("sandwich")
        animated.begin_action("eat", time.monotonic())
        overlay = animated.food_overlay
        self.assertEqual(self.canvas.itemcget(overlay.item, "state"), "normal")
        positions: list[tuple[float, ...]] = []
        for index, frame in enumerate(clip.frames):
            animated.show_frame("eat", time.monotonic(), fixed=index)
            positions.append(tuple(self.canvas.coords(overlay.item)))
            self.assertEqual(self.canvas.itemcget(overlay.item, "state"),
                             "normal")
            self.assertIsNotNone(frame.food_anchor)
        self.assertGreater(len(set(positions)), 2)
        animated.show_frame("idle", time.monotonic(), fixed=0)
        self.assertEqual(self.canvas.itemcget(overlay.item, "state"), "hidden")

    def test_onigiri_overlaps_the_eating_grip_in_front_of_the_character(self) -> None:
        animated = self.anim
        clip = animated.assets.clips["eat"]
        overlay = animated.food_overlay
        # Finger contact positions measured on the eight approved source poses.
        hand_y = (153, 135, 129, 135, 135, 135, 153, 153)
        overlay.select("onigiri")
        for scale in (1, 2):
            for index, frame in enumerate(clip.frames):
                with self.subTest(scale=scale, frame=index):
                    overlay.render(clip, frame, scale=scale)
                    left, top = self.canvas.coords(overlay.item)
                    image = overlay._images[("onigiri", scale)]
                    x = round((192 // 2 - clip.anchor[0] + 96) * scale - left)
                    y = round((FOOT_BASELINE - clip.anchor[1] + hand_y[index])
                              * scale - top)
                    self.assertTrue(0 <= x < image.width())
                    self.assertTrue(0 <= y < image.height())
                    self.assertFalse(image.transparency_get(x, y))
                    stack = self.canvas.find_all()
                    self.assertGreater(stack.index(overlay.item),
                                       stack.index(animated.image_item))

    def test_consumables_stay_above_hands_during_pickup_holding_and_putdown(self):
        animated = self.anim
        overlay = animated.food_overlay
        for food in ("onigiri", "energy_drink"):
            overlay.select(food)
            for scale in (1, 2):
                for clip_name in ("pick_up", "put_down"):
                    clip = animated.assets.clips[clip_name]
                    for index, frame in enumerate(clip.frames):
                        if frame.food_anchor is None:
                            continue
                        with self.subTest(food=food, scale=scale, clip=clip_name,
                                          frame=index):
                            overlay.render(clip, frame, scale=scale)
                            self.assertEqual(self.canvas.find_all()[-1],
                                             overlay.item)
