"""Relationship, compound need, authored coverage and story rotation contracts."""

from __future__ import annotations

import random
import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import patch

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.controller import CareController
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.balance import parse_balance
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.dialogue_context import (
    FriendshipStage,
    ReactionTone,
    SituationalCondition,
)
from aiko_pet.pet.needs import NeedCondition
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from tools.dialogue_test_support import (
    balance_source_fixture,
    dialogue_context,
    dialogue_source_fixture,
)
from tools.pet_test_support import set_test_pet_values


class DialogueContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.time = context_at(datetime(2026, 10, 16, 15).timestamp())
        self.mind = make_aiko_mind(started_at=0, rng=random.Random(7))

    def test_relationship_boundaries_follow_display_levels(self) -> None:
        expected = ["acquaintance"] * 2 + ["familiar"] * 3
        expected += ["friend"] * 3 + ["close"] * 2
        for level, stage in enumerate(expected, 1):
            self.assertEqual(FriendshipStage.from_level(level), stage)
            state = PetState(friendship=(level - 1) * 10)
            self.assertEqual(
                self.mind.dialogue_context(state, self.time, 10).stage,
                stage,
            )

    def test_multiple_needs_survive_the_primary_emotion(self) -> None:
        state = PetState(energy=10, satiety=10, social=10, affection=10)
        snapshot = self.mind.dialogue_context(state, self.time, 10)
        self.assertEqual(snapshot.emotions.primary, EmotionalState.SATISFIED)
        self.assertEqual(
            snapshot.need_conditions,
            {
                NeedCondition.LOW_ENERGY,
                NeedCondition.LOW_SATIETY,
                NeedCondition.LOW_SOCIAL,
                NeedCondition.LOW_AFFECTION,
            },
        )

    def test_care_uses_the_entire_pre_effect_context(self) -> None:
        state = PetState(energy=15, satiety=10, friendship=19.9)
        controller = CareController(
            state,
            self.mind,
            AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        )
        inputs = SessionInputs(
            self.time.local.timestamp(),
            10,
            False,
            False,
            False,
            False,
            None,
        )
        with patch.object(
            self.mind,
            "select_reaction",
            wraps=self.mind.select_reaction,
        ) as select:
            outcome = controller.execute(CareCommand.from_action("feed"), inputs)
        snapshot = select.call_args.kwargs["dialogue"]
        self.assertEqual(snapshot.stage, FriendshipStage.ACQUAINTANCE)
        self.assertIn(NeedCondition.LOW_SATIETY, snapshot.need_conditions)
        self.assertGreater(state.satiety, 25)
        assert outcome.reaction is not None
        selected = next(
            x for x in self.mind.book.lines if x.id == outcome.reaction.line_id
        )
        self.assertEqual(
            selected.conditions[0].need_conditions,
            {NeedCondition.LOW_SATIETY, NeedCondition.LOW_ENERGY},
        )

    def test_fallback_never_borrows_from_another_relationship(self) -> None:
        book = self.mind.book
        for stage in FriendshipStage:
            snapshot = dialogue_context(self.time, stage=stage, present=True)
            for i in range(30):
                chosen = book.choose("pet", snapshot, i, presentation="short")
                assert chosen is not None
                line = next(x for x in book.lines if x.id == chosen.line_id)
                self.assertIn(stage, line.stages)

    def test_48_stories_have_single_emotion_and_desktop_stage_distribution(
        self,
    ) -> None:
        stories = [x for x in self.mind.book.lines if x.presentation == "story"]
        self.assertEqual(len(stories), 48)
        for stage in FriendshipStage:
            selected = [x for x in stories if x.stages == (stage,)]
            self.assertEqual(len(selected), 12)
            self.assertEqual(
                sum(
                    any(
                        SituationalCondition.FATIGUED in c.situational_conditions
                        for c in x.conditions
                    )
                    for x in selected
                ),
                2,
            )
            self.assertEqual(
                sum(
                    any(ReactionTone.WARM in c.reaction_tones for c in x.conditions)
                    for x in selected
                ),
                1,
            )
            for line in selected:
                self.assertTrue(line.conditions)
                self.assertTrue(3 <= sum(b.kind == "text" for b in line.beats) <= 5)
                self.assertTrue(any(b.kind == "emote" for b in line.beats))

    def test_story_rotation_exhausts_the_matching_pool(self) -> None:
        snapshot = dialogue_context(
            self.time, stage=FriendshipStage.FRIEND, present=True
        )
        pool = {
            x.id
            for x in self.mind.book.lines
            if x.event == "talk" and x.presentation == "story" and x.matches(snapshot)
        }
        ids = []
        for i in range(len(pool)):
            chosen = self.mind.book.choose("talk", snapshot, i, presentation="story")
            assert chosen is not None
            ids.append(chosen.line_id)
        self.assertEqual(set(ids), pool)
        self.assertEqual(len(ids), len(set(ids)))

    def test_warm_stories_do_not_borrow_calm_dialogue(self) -> None:
        for stage in FriendshipStage:
            warm = dialogue_context(
                self.time, stage=stage, reaction_tone=ReactionTone.WARM, present=True
            )
            calm = dialogue_context(self.time, stage=stage, present=True)
            pool = [
                line
                for line in self.mind.book.lines
                if line.presentation == "story"
                and line.matches(warm)
                and any(ReactionTone.WARM in c.reaction_tones for c in line.conditions)
            ]
            self.assertEqual(len(pool), 1)
            self.assertTrue(
                any(ReactionTone.WARM in c.reaction_tones for c in pool[0].conditions)
            )
            self.assertFalse(pool[0].matches(calm))
            chosen = self.mind.book.choose("talk", warm, 1, presentation="story")
            assert chosen is not None
            self.assertEqual(chosen.line_id, pool[0].id)

    def test_single_primary_emotion_per_authored_variant(self) -> None:
        self.assertTrue(
            all(
                isinstance(c.emotional_states, frozenset)
                for line in self.mind.book.lines
                for c in line.conditions
            )
        )
        for stage in FriendshipStage:
            for emotion in (EmotionalState.SUBDUED, EmotionalState.IRRITATED):
                snapshot = dialogue_context(
                    self.time, stage=stage, emotional_state=emotion, present=True
                )
                pool = [
                    line
                    for line in self.mind.book.lines
                    if line.event == "talk"
                    and line.presentation == "story"
                    and line.matches(snapshot)
                ]
                self.assertEqual(len(pool), 1, (stage, emotion))

    def test_spontaneous_story_throttle_and_sleep(self) -> None:
        state = PetState(friendship=90, mood=65, social=80, affection=80)
        context = self.mind.dialogue_context(state, self.time, 10, present=True)
        raw = balance_source_fixture()
        raw["dialogue"]["spontaneous_story_quiet_seconds"] = 60
        raw["dialogue"]["spontaneous_story_probability"] = 0.05
        with (
            patch("aiko_pet.pet.mind.mind.BALANCE", parse_balance(raw)),
            patch.object(self.mind, "dialogue_context", return_value=context),
            patch.object(self.mind, "_select_spontaneous_event", return_value="idle"),
            patch.object(self.mind.rng, "random", return_value=0.049),
        ):
            first = self.mind.select_spontaneous_reaction(state, self.time, 10)
            second = self.mind.select_spontaneous_reaction(state, self.time, 69)
            third = self.mind.select_spontaneous_reaction(state, self.time, 70)
            assert first and second and third
            self.assertEqual(first.presentation, "story")
            self.assertEqual(second.presentation, "short")
            self.assertEqual(third.presentation, "story")
            with patch.object(self.mind.rng, "random", return_value=0.05):
                chosen = self.mind.select_spontaneous_reaction(state, self.time, 130)
                assert chosen is not None
                self.assertEqual(chosen.presentation, "short")
        with patch.object(self.mind.rng, "random", return_value=0.2):
            self.mind._last_spontaneous_story = -1000
            chosen = self.mind.select_spontaneous_reaction(state, self.time, 1000)
            assert chosen is not None
            self.assertEqual(chosen.presentation, "short")
        set_test_pet_values(state, sleeping=True)
        self.assertIsNone(self.mind.select_spontaneous_reaction(state, self.time, 2000))

    def test_short_catalogue_coverage_in_every_relationship(self) -> None:
        book = self.mind.book
        events = {x.event for x in book.lines if x.presentation == "short"}
        for stage in FriendshipStage:
            for event in events:
                lines = [
                    x
                    for x in book.lines
                    if x.event == event and x.presentation == "short"
                ]
                # Use the event's authored day/period, not an impossible trigger.
                sample = lines[0]
                candidates = [x for x in lines if not x.stages or stage in x.stages]
                self.assertTrue(candidates, (stage, event, sample.id))
                if event in {
                    "click_left",
                    "click_right",
                    "rapid_click",
                    "pet",
                    "feed_meal",
                    "play",
                    "sleep",
                    "wake",
                    "talk",
                }:
                    self.assertGreaterEqual(len(candidates), 3, (stage, event))

    def test_rejects_bad_sequences_filters_and_placeholders(self) -> None:
        original = dialogue_source_fixture()["lines"][0]
        invalid = [
            {"beats": []},
            {"stages": ["romantic"]},
            {"conditions": [{"need_conditions": ["invented"]}]},
            {"beats": [{"kind": "emote", "content": "invented"}]},
            {"beats": [{"kind": "text", "content": "A" * 126}]},
            {"beats": [{"kind": "text", "content": "{unknown}"}]},
            {"beats": [{"kind": "pause", "duration_ms": True}]},
            {"beats": [{"kind": "text", "content": "A", "duration_ms": 1}]},
            {"followup_text": "old schema"},
        ]
        for update in invalid:
            with self.subTest(update=update), self.assertRaises(ValueError):
                Line.parse(dict(original, **update))
        line = self.mind.book.lines[0]
        unavailable = replace(line, stages=(FriendshipStage.CLOSE,))
        book = DialogueBook((unavailable,))
        snapshot = dialogue_context(self.time)
        self.assertIsNone(book.choose(line.event, snapshot, 10))
