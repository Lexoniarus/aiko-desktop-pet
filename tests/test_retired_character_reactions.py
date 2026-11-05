"""Retired body gestures never replace the approved V3 communication clips."""

import unittest
from dataclasses import replace
from unittest.mock import MagicMock

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.activity import ActivityCallbacks, ActivityCoordinator
from aiko_pet.application.settings import PetSettings
from aiko_pet.frontend.playback import ReactionPlayer
from aiko_pet.pet.animation.expression import Expression
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind import PetMind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.catalog import DialogueBook, Line, Reaction
from aiko_pet.pet.mind.dialogue_context import (
    DialogueContext,
    FriendshipStage,
    ReactionTone,
)
from aiko_pet.pet.mind.expression_policy import speech_expression
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from tools.reaction_test_support import FakeScheduler


class RetiredCharacterReactionTests(unittest.TestCase):
    def setUp(self):
        self.context = DialogueContext(
            FriendshipStage.FRIEND, 50, EmotionalComposition(EmotionalState.CALM),
            context_at(1_800_000_000),
        )

    def test_catalogue_has_no_retired_actions_and_keeps_real_body_gestures(self):
        book = DialogueBook.from_file()
        actions = {line.animation for line in book.lines}
        self.assertFalse(actions & {"review", "failed"})
        self.assertTrue({"waiting", "waving", "jumping"} <= actions)

    def test_selected_replacements_start_only_at_text_without_a_body_action(self):
        lines = {line.id: line for line in DialogueBook.from_file().lines}
        for identity, expression in (
            ("v010-click_sleepy-02", Expression.QUESTIONING),
            ("v010-click_weary-01", Expression.FIRM),
            ("v010-click_work_boundary-01", Expression.FIRM),
            ("v010-work_late-01", Expression.WORRIED),
            ("v010-work_finished_long-03", Expression.POSITIVE),
        ):
            with self.subTest(identity=identity):
                line = replace(lines[identity], conditions=(), stages=(),
                               periods=(), weekdays=())
                reaction = DialogueBook((line,)).choose(line.event, self.context, 100)
                assert reaction is not None
                self.assertEqual(reaction.animation, "idle")
                self.assertEqual(reaction.expression, expression)
                self.assertEqual(reaction.beats, line.beats)

                scheduler, trace, actions = FakeScheduler(), [], []
                player = ReactionPlayer(
                    schedule=scheduler.schedule, cancel_timer=scheduler.cancel,
                    display_text=lambda text, _ms: trace.append(("text", text)),
                    display_emote=lambda *_: None, mark_spoken=lambda: None,
                    is_closed=lambda: False, start_action=lambda *a: actions.append(a),
                    express=lambda face: trace.append(("face", face)),
                )
                player.play(reaction)
                while not any(kind == "text" for kind, _ in trace):
                    assert player.pending_timer is not None
                    scheduler.fire(player.pending_timer)
                first_text = next(i for i, row in enumerate(trace) if row[0] == "text")
                self.assertEqual(trace[first_text - 1], ("face", expression))
                self.assertEqual(actions, [])
                player.cancel()

    def test_retired_animation_names_and_invalid_authored_faces_are_rejected(self):
        raw = dict(id="test", event="click_left", animation="idle", periods=[],
                   weekdays=[], beats=[dict(kind="text", content="Ja?")])
        for fields in ({"animation": "review"}, {"animation": "failed"},
                       {"expression": "unknown"}, {"expression": True},
                       {"expression": None}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                Line.parse(raw | fields)
        self.assertEqual(Line.parse(raw | {"expression": "questioning"}).expression,
                         Expression.QUESTIONING)

    def test_authored_face_does_not_override_a_boundary_or_explicit_game_outcome(self):
        self.assertEqual(speech_expression(
            "click_left", replace(self.context, reaction_tone=ReactionTone.IRRITATED),
            authored=Expression.POSITIVE,
        ), Expression.FIRM)
        self.assertEqual(speech_expression(
            "game_player_win", self.context, authored=Expression.POSITIVE,
        ), Expression.DOWNCAST)


class WorkloadCommunicationTests(unittest.TestCase):
    def test_workload_waits_for_speech_without_a_preliminary_body_action(self):
        mind = MagicMock(spec=PetMind)
        reaction = Reaction("work", (Cue.text("Ich bleibe dran."),), "idle",
                            "computer_effort_steady", expression=Expression.WORRIED)
        mind.select_computer_reaction.return_value = reaction
        events = MagicMock(spec=WorkloadEventDetector)
        events.observe_change.return_value = "computer_effort_steady"
        monitor = MagicMock()
        monitor.latest.return_value = ComputerSnapshot(cpu=95, measured_at=100)
        shown = []
        busy = True
        activity = ActivityCoordinator(
            PetState(), PetSettings(observe_computer=True, spontaneous_talk=True),
            mind, AdaptiveRoutine(), events, monitor,
            ActivityCallbacks(
                read_idle_seconds=lambda: 0, react=lambda r, _ms: shown.append(r),
                action_until=lambda: 0, last_spoken=lambda: -1000,
                speech_busy=lambda: busy,
            ), clock=ActiveSessionClock(lambda: 0),
        )
        before = activity.state.capture_checkpoint()
        context = context_at(1_800_000_000)
        activity.react_to_computer(100, context)
        self.assertEqual(shown, [])
        mind.select_computer_reaction.assert_not_called()
        self.assertEqual(activity.pending_computer_line,
                         ("computer_effort_steady", 100))
        busy = False
        activity.react_to_computer(101, context)
        self.assertEqual(shown, [reaction])
        self.assertIsNone(activity.pending_computer_line)
        self.assertEqual(activity.state.capture_checkpoint(), before)
