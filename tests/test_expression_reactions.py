"""Actual cue admission/cancellation and independent minigame face requests."""

import unittest
from unittest.mock import MagicMock

from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.pet.animation.expression import Expression
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.ui.windows.game_speech import GameSpeech
from tools.reaction_test_support import FakeScheduler


class ExpressionReactionTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = FakeScheduler()
        self.expressions, self.actions = [], []
        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule, cancel_timer=self.scheduler.cancel,
            display_text=lambda *_args: None, display_emote=lambda *_args: None,
            start_action=lambda *args: self.actions.append(args),
            mark_spoken=lambda: None, is_closed=lambda: False,
            express=self.expressions.append,
        )

    def test_face_begins_at_authored_beat_without_starting_a_body_action(self):
        self.player.play(Reaction(
            "test", (Cue.text("Erst zuhören."), Cue.text("Jetzt die Reaktion.")),
            "idle", "talk", expression=Expression.QUESTIONING, expression_at=1,
        ))
        self.assertEqual(self.expressions, [None])
        assert self.player.pending_timer is not None
        self.scheduler.fire(self.player.pending_timer)
        self.assertEqual(self.expressions, [None, Expression.QUESTIONING])
        self.assertEqual(self.actions, [])

    def test_cancelled_and_already_queued_cues_cannot_revive_a_face(self):
        self.player.play(Reaction(
            "test", (Cue.text("Erst zuhören."), Cue.text("Spätere Reaktion.")),
            "idle", "talk", expression=Expression.FIRM, expression_at=1,
        ))
        assert self.player.pending_timer is not None
        stale = self.scheduler.callbacks[self.player.pending_timer][1]
        self.player.cancel()
        stale()
        self.assertEqual(self.expressions, [None, None])

    def test_joke_smile_waits_until_complete_provider_text_has_been_displayed(self):
        payload = dict(
            error=False, safe=True, lang="de", id=30, type="twopart",
            category="Programming", setup="Wieso läuft der Rechner?",
            delivery="Weil er sich die Beine vertritt.",
            flags=dict.fromkeys(
                ("nsfw", "racist", "sexist", "religious", "political", "explicit"),
                False,
            ),
        )
        reaction = prepare_social_content(SocialCategory.TWO_PARTS, payload).reaction
        last_text = max(i for i, beat in enumerate(reaction.beats)
                        if beat.kind == "text")
        self.assertGreater(reaction.expression_at, last_text)
        self.player.play(reaction)
        for _ in range(reaction.expression_at):
            self.assertNotIn(Expression.POSITIVE, self.expressions)
            assert self.player.pending_timer is not None
            self.scheduler.fire(self.player.pending_timer)
        self.assertEqual(self.expressions[-1], Expression.POSITIVE)

    def test_game_expression_is_not_a_body_clip_and_joy_hop_is_retained(self):
        animate, express = MagicMock(), MagicMock()
        speech = GameSpeech(self.player, MagicMock(), lambda: None,
                            lambda _enabled: None, animate, express)
        speech.animate("expression-downcast")
        express.assert_called_once_with(Expression.DOWNCAST)
        animate.assert_not_called()
        speech.animate("jumping")
        express.assert_called_with(None)
        animate.assert_called_once_with("jumping")
        speech.stop()
        express.assert_called_with(None)
