"""Facial clips yield to actual gaze/actions and never queue stale reactions."""

import unittest
from dataclasses import replace
from types import MappingProxyType

from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.pet.animation.animation import SpriteSelection
from aiko_pet.pet.animation.expression import (
    EXPRESSION_CLIPS,
    Expression,
    event_expression,
)
from aiko_pet.pet.animation.expression_playback import ExpressionPlayback
from aiko_pet.pet.animation.priority import RenderDecision


class ExpressionPlaybackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_character_catalog()

    def setUp(self):
        self.player = ExpressionPlayback(self.catalog)
        self.base = RenderDecision(SpriteSelection("idle", 0), clear_action=True)
        self.select(100)

    def select(self, now, *, base=None, blinking=False):
        return self.player.select(base or self.base, now, blinking=blinking)

    def test_every_reaction_shows_all_eight_authored_phases_even_on_late_ticks(self):
        for expression in Expression:
            if expression == Expression.NEUTRAL:
                continue
            with self.subTest(expression=expression):
                self.assertTrue(self.player.request(expression))
                clip = self.catalog.expression_clips[EXPRESSION_CLIPS[expression]]
                now = 100.0
                for index, frame in enumerate(clip.frames):
                    decision, finished = self.select(now)
                    self.assertEqual(decision.sprite, SpriteSelection(clip.name, index))
                    self.assertTrue(decision.clear_action)
                    self.assertFalse(finished)
                    now += frame.duration_ms / 1000 + .15
                result, _ = self.select(now)
                self.assertEqual(result.sprite, SpriteSelection("rest-neutral", 0))

    def test_incompatible_pose_discards_reaction_and_does_not_replay_on_return(self):
        for pose in (SpriteSelection("look", 12), SpriteSelection("body-look-left", 2),
                     SpriteSelection("body-step-right-profil"),
                     SpriteSelection("running-right"), SpriteSelection("pick_up", 7),
                     SpriteSelection("sleep"), SpriteSelection("jumping")):
            with self.subTest(pose=pose):
                self.select(100)
                self.assertTrue(self.player.request(Expression.POSITIVE))
                self.select(100.1)
                base = RenderDecision(pose, playback_rate=1.4, reverse=True)
                self.assertEqual(self.select(100.2, base=base), (base, False))
                self.assertFalse(self.player.request(Expression.WORRIED))
                self.assertEqual(self.select(101)[0].sprite,
                                 SpriteSelection("rest-neutral", 0))

    def test_gaze_cancels_communication_and_returns_to_neutral_rest(self):
        self.player.request(Expression.POSITIVE)
        self.select(100, base=RenderDecision(SpriteSelection("look", 3)))
        result, _ = self.select(101)
        self.assertEqual(result.sprite, SpriteSelection("rest-neutral", 0))
        result, _ = self.select(102)
        self.assertEqual(result.sprite, SpriteSelection("rest-neutral", 0))

    def test_blink_uses_only_eye_phases_and_returns_to_neutral_rest(self):
        for now, index in ((100, 2), (100.07, 3), (100.17, 4)):
            result, finished = self.select(now, blinking=True)
            self.assertEqual(result.sprite, SpriteSelection("rest-neutral", index))
            self.assertFalse(finished)
        result, finished = self.select(100.25, blinking=True)
        self.assertTrue(finished)
        self.assertEqual(result.sprite, SpriteSelection("rest-neutral", 0))

    def test_cancel_consumes_only_visual_reaction(self):
        self.player.request(Expression.FIRM)
        self.select(100)
        self.assertFalse(self.player.request(None))
        self.assertEqual(self.select(101)[0].sprite, SpriteSelection("rest-neutral", 0))

    def test_legacy_installations_keep_existing_blink_and_body_policies(self):
        player = ExpressionPlayback(replace(
            self.catalog, expression_clips=MappingProxyType({}),
        ))
        self.assertEqual(player.select(self.base, 100, blinking=True),
                         (self.base, False))
        self.assertFalse(player.request(Expression.POSITIVE))

    def test_event_faces_still_require_an_explicit_semantic_request(self):
        self.assertEqual(event_expression("cursor_notice_playful"),
                         Expression.QUESTIONING)
        self.assertEqual(event_expression("cursor_fear_response"), Expression.WORRIED)
        self.assertIsNone(event_expression("some_text_with_happy_words"))
