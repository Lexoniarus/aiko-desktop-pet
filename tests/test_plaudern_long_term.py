"""Care-period feelings stay distinct from an invented individual experience."""

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_long_term_moodlets import DAY, HOUR, contact, evaluate, upsetting
from test_plaudern import talk

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.care_evidence import CareActivity
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.conversation_topics import (
    LONG_TERM_FAMILIES,
    ConversationKind,
    ConversationTopic,
)
from aiko_pet.pet.mind.dialogue_context import FriendshipStage
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from tools.dialogue_test_support import dialogue_context
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import require_test_value

WALL = 1800000000


def real_periods():
    good = evaluate((
        contact("a", 0, wish=1),
        contact("b", 4 * HOUR, CareActivity.PETTING, wish=2),
        contact("c", 8 * HOUR, CareActivity.PLAY, wish=3, win=True),
    ))
    uncertain = evaluate((
        contact("a", 0),
        upsetting("bad-a", HOUR),
        contact("b", 4 * HOUR),
        upsetting("bad-b", 5 * HOUR),
    ))
    guarded = evaluate(tuple(upsetting(str(n), (1 + 2 * n) * HOUR) for n in range(3)))
    overlooked = evaluate(())
    return {
        episode.definition_id: (state, episode)
        for state in (good, uncertain, guarded, overlooked)
        for episode in state.active
        if episode.definition_id in LONG_TERM_FAMILIES
    }


class PlaudernLongTermTests(unittest.TestCase):
    def setUp(self):
        self.book = DialogueBook.from_file(rng=random.Random(0))
        self.periods = real_periods()

    def test_all_six_real_patterns_have_relationship_and_emotional_variants(self):
        self.assertEqual(set(self.periods), LONG_TERM_FAMILIES)
        for family, (_state, episode) in self.periods.items():
            cause = episode.causes[0]
            self.assertIsNotNone(cause.period)
            normal = set()
            for stage in FriendshipStage:
                for emotion in (
                    EmotionalState.CALM,
                    EmotionalState.DOWNCAST,
                    EmotionalState.AMBIVALENT,
                ):
                    context = replace(
                        dialogue_context(context_at(WALL), stage=stage),
                        emotions=EmotionalComposition(emotion),
                        conversation_topic=ConversationTopic(
                            ConversationKind.LONG_TERM,
                            episode.instance_id,
                            family,
                            cause,
                        ),
                    )
                    reaction = require_test_value(self.book.choose("talk", context, 10))
                    self.assertIn(f"long-term-{family.value}", reaction.line_id)
                    text = " ".join(
                        b.content for b in reaction.beats if b.kind == "text"
                    )
                    self.assertNotIn("absichtlich", text)
                    self.assertNotIn("Mastermind", text)
                    self.assertNotIn("Donut", text)
                    self.assertFalse(any(char.isdigit() for char in text))
                    if emotion == EmotionalState.CALM:
                        normal.add(reaction.line_id)
                    else:
                        self.assertIn(
                            "mixed"
                            if emotion == EmotionalState.AMBIVALENT
                            else "quiet",
                            reaction.line_id,
                        )
            self.assertEqual(len(normal), 4)

    def test_saved_period_remains_a_feeling_after_raw_events_are_removed(self):
        state, episode = self.periods[MoodletId.TRUSTING]
        evidence = require_test_value(state.care_evidence)
        state = replace(
            state, active=(episode,), care_evidence=replace(evidence, experiences=())
        )
        pet = PetState(updated_at=WALL, lived_seconds=DAY, moodlets=state)
        before = pet.capture_checkpoint()
        self.assertIn("long-term-trusting", talk(pet).line_id)
        self.assertEqual(pet.capture_checkpoint(), before)
        with tempfile.TemporaryDirectory(prefix="aiko-period-story-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            loaded = SqliteStateStore(path).load_session(now=WALL).state
            self.assertEqual(loaded.moodlets, pet.moodlets)
            self.assertIn("long-term-trusting", talk(loaded).line_id)

    def test_unknown_legacy_pattern_does_not_become_an_invented_care_history(self):
        episode = MoodletEpisode(1, MoodletId.TRUSTING, 1, 0, 0, 600)
        pet = PetState(
            updated_at=WALL,
            lived_seconds=100,
            moodlets=MoodletState(next_instance_id=2, active=(episode,)),
        )
        self.assertTrue(talk(pet).line_id.startswith("plaudern-state-"))

    def test_period_stories_cannot_render_a_particular_gift_or_internal_counter(self):
        raw = dict(
            id="bad-period",
            event="talk",
            animation="idle",
            presentation="story",
            periods=[],
            weekdays=[],
        )
        for text in ("{target}", "{count}", "{source_quote}"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                Line.parse(
                    dict(
                        raw,
                        conditions=[
                            dict(
                                conversation_topics=["long_term.appreciated"],
                                conversation_targets=["apple"],
                            )
                        ],
                        beats=[dict(kind="text", content=text)],
                    )
                )


if __name__ == "__main__":
    unittest.main()
