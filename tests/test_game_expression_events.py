"""All six game sequences attach semantic facial intent at real speech time."""

import unittest
from dataclasses import replace
from typing import Any
from unittest.mock import MagicMock

from aiko_pet.games.quiz import QuizSession
from aiko_pet.games.quiz_catalogue import QuizCatalogue
from aiko_pet.pet.animation.expression import Expression, event_expression
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.conversation_topics import ConversationKind, ConversationTopic
from aiko_pet.pet.mind.dialogue_context import DialogueContext, FriendshipStage
from aiko_pet.pet.mind.expression_policy import speech_expression
from aiko_pet.pet.moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletId,
    MoodletOutcome,
)
from aiko_pet.pet.routine import context_at
from aiko_pet.ui.windows.blackjack_sequence import BlackjackSequence
from aiko_pet.ui.windows.connect_four_sequence import ConnectFourSequence
from aiko_pet.ui.windows.game_speech import GameSpeech
from aiko_pet.ui.windows.mastermind_sequence import MastermindSequence
from aiko_pet.ui.windows.quiz_sequence import QuizSequence
from aiko_pet.ui.windows.rock_paper_scissors_sequence import RockPaperScissorsSequence
from aiko_pet.ui.windows.tic_tac_toe_sequence import TicTacToeSequence
from tools.reaction_test_support import FakeScheduler


class GameExpressionEventsTests(unittest.TestCase):
    def test_normal_speech_gets_a_short_face_without_forcing_the_idle_expression(self):
        raw = dict(
            id="speech", event="talk", animation="idle", periods=[], weekdays=[],
            conditions=[dict(conversation_topics=["state"])],
            beats=[dict(kind="emote", content="question", duration_ms=500),
                   dict(kind="text", content="Ich erzähle dir davon.")],
        )
        book = DialogueBook((Line.parse(raw),))
        for feeling, expected in ((EmotionalState.SATISFIED, Expression.POSITIVE),
                                  (EmotionalState.SUBDUED, Expression.DOWNCAST),
                                  (EmotionalState.TENSE, Expression.WORRIED)):
            context = DialogueContext(FriendshipStage.FRIEND,
                                      75 if feeling == EmotionalState.SATISFIED else 35,
                                      EmotionalComposition(feeling),
                                      context_at(1_800_000_000),
                                      conversation_topic=ConversationTopic(
                                          ConversationKind.STATE,
                                      ))
            reaction = book.choose("talk", context, 100)
            assert reaction is not None
            self.assertEqual(reaction.expression, expected)
            self.assertEqual(reaction.expression_at, 1)

    def test_positive_history_stays_a_topic_without_overriding_the_actual_feeling(self):
        context = DialogueContext(FriendshipStage.FRIEND, 35,
                                  EmotionalComposition(EmotionalState.SUBDUED),
                                  context_at(1_800_000_000),
                                  conversation_topic=ConversationTopic(
                                      ConversationKind.LONG_TERM,
                                      moodlet_id=MoodletId.APPRECIATED,
                                  ))
        self.assertEqual(speech_expression("talk", context), Expression.DOWNCAST)
        assert context.conversation_topic is not None
        self.assertEqual(context.conversation_topic.moodlet_id, MoodletId.APPRECIATED)

    def test_all_six_greetings_attach_intent_to_actual_text(self):
        for kind in (RockPaperScissorsSequence, TicTacToeSequence, BlackjackSequence,
                     ConnectFourSequence, MastermindSequence, QuizSequence):
            with self.subTest(game=kind.__name__):
                clock, trace = FakeScheduler(), []
                kwargs: dict[str, Any] = dict(
                    schedule=clock.schedule, cancel=clock.cancel,
                    present=lambda *_: None,
                    say=lambda text, _ms: trace.append(("text", text)),
                    animate=lambda _clip: None, dialogue=lambda event: event,
                    express_event=lambda event: trace.append(("expression", event)),
                )
                if kind is RockPaperScissorsSequence:
                    kwargs.pop("present")
                    kwargs.update(show_emote=lambda *_: None,
                                  show_aiko_hand=lambda *_: None,
                                  reveal_player=lambda *_: None,
                                  set_busy=lambda _: None)
                if kind is BlackjackSequence:
                    kwargs["hand"] = lambda *_: None
                if kind in (ConnectFourSequence, MastermindSequence, QuizSequence):
                    kwargs["emote"] = lambda *_: None
                if kind is MastermindSequence:
                    kwargs.update(show_code=lambda *_: None, hide_code=lambda: None)
                flow = (QuizSequence(QuizSession(QuizCatalogue.load()), **kwargs)
                        if kind is QuizSequence else kind(**kwargs))
                try:
                    flow.greet()
                    self.assertEqual(len(trace), 2)
                    self.assertEqual(trace[0][0], "expression")
                    self.assertEqual(trace[1], ("text", trace[0][1]))
                    self.assertIsNotNone(event_expression(trace[0][1]))
                finally:
                    flow.close()

    def test_delayed_or_cancelled_speech_does_not_trigger_a_premature_expression(self):
        clock, trace = FakeScheduler(), []
        flow = MastermindSequence(
            schedule=clock.schedule, cancel=clock.cancel, present=lambda *_: None,
            show_code=lambda _: None, hide_code=lambda: None, say=lambda *_: None,
            animate=lambda _: None, emote=lambda *_: None, dialogue=lambda event: event,
            express_event=trace.append,
        )
        flow._react("game_mm_last", emote="question")
        self.assertEqual(trace, [])
        assert flow.pending_timer is not None
        stale = clock.callbacks[flow.pending_timer][1]
        flow.close()
        stale()
        self.assertEqual(trace, [])

    def test_game_roles_and_retained_aiko_perspective_are_explicit(self):
        context = DialogueContext(FriendshipStage.FRIEND, 35,
                                  EmotionalComposition(EmotionalState.SUBDUED),
                                  context_at(1_800_000_000))
        for target, result, expression in (
            ("blackjack", MoodletOutcome.WIN, Expression.POSITIVE),
            ("blackjack", MoodletOutcome.LOSS, Expression.DOWNCAST),
            ("mastermind", MoodletOutcome.LOSS, Expression.POSITIVE),
            ("mastermind", MoodletOutcome.WIN, Expression.WORRIED),
            ("quiz", MoodletOutcome.COMPLETED, Expression.POSITIVE),
        ):
            cause = MoodletCause(MoodletCauseKind.INTERACTION, 0,
                                 target_id=target, outcome=result)
            topic = ConversationTopic(ConversationKind.GAME, cause=cause)
            self.assertEqual(speech_expression("talk", replace(
                context, conversation_topic=topic,
            )), expression)
        self.assertEqual(event_expression("game_round_player_win"), Expression.DOWNCAST)
        self.assertEqual(event_expression("game_mm_player_win"), Expression.POSITIVE)

    def test_returning_to_idle_does_not_cancel_the_current_spoken_reaction(self):
        express, animate = MagicMock(), MagicMock()
        speech = GameSpeech(MagicMock(), MagicMock(), lambda: None,
                            lambda _: None, animate, express)
        speech.react("game_round_player_win")
        speech.say("Diese Runde geht an dich.", 2000)
        speech.animate("idle")
        express.assert_called_once_with(Expression.DOWNCAST)
        speech.animate("jumping")
        express.assert_called_with(None)
        speech.stop()
        express.assert_called_with(None)
