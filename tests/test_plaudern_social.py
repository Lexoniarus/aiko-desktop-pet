"""Actual told words are quoted, never paraphrased or attributed to the user."""

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_plaudern import talk
from test_social_content import fact_payload
from test_social_evidence_playback import originals, play_content
from test_wish_assignment import wish
from test_wish_social_assignment import WALL, SocialHarness

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.conversation_topics import ConversationKind, ConversationTopic
from aiko_pet.pet.mind.dialogue_context import FriendshipStage
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.wishes import WishId
from tools.dialogue_test_support import dialogue_context
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import require_test_value


def choose_social(
    book, cause, *, stage=FriendshipStage.FRIEND, emotion=EmotionalState.CALM
):
    context = replace(
        dialogue_context(context_at(WALL), stage=stage),
        emotions=EmotionalComposition(emotion),
        conversation_topic=ConversationTopic(
            ConversationKind.SOCIAL,
            1,
            MoodletId.CONNECTION,
            cause,
        ),
    )
    return require_test_value(book.choose("talk", context, 10, presentation="story"))


class PlaudernSocialTests(unittest.TestCase):
    def setUp(self):
        self.book = DialogueBook.from_file(rng=random.Random(0))

    def test_full_playback_retains_original_parts_author_and_bounded_source_references(
        self,
    ):
        for item in originals():
            with self.subTest(category=item.category, provider=item.provider):
                harness = SocialHarness(wish(WishId(item.category), item.category))
                play_content(harness, item)
                self.assertFalse(harness.pet.moodlets.active)
                harness.finish()
                cause = harness.pet.moodlets.active[0].causes[0]
                checkpoint = harness.pet.capture_checkpoint()
                reaction = talk(harness.pet)
                self.assertTrue(reaction.line_id.startswith("plaudern-social-"))
                texts = [b.content for b in reaction.beats if b.kind == "text"]
                quotes = [text for text in texts if text.startswith("»")]
                content = require_test_value(item.evidence)
                self.assertEqual(len(quotes), len(content.parts))
                for quote, part in zip(quotes, content.parts, strict=True):
                    self.assertTrue(quote.endswith("«"))
                    body = quote[1:-1]
                    if body.endswith("…"):
                        self.assertTrue(part.startswith(body[:-1]))
                    else:
                        self.assertEqual(body, part)
                if content.kind == "quotation":
                    self.assertIn(f"Von {content.author}.", texts)
                self.assertTrue(all(len(text) <= 125 for text in texts))
                self.assertLessEqual(len(texts), 5)
                self.assertEqual(harness.pet.capture_checkpoint(), checkpoint)
                self.assertIs(cause.social_content, item.evidence)
                self.assertFalse(
                    any("du hast gelacht" in text.lower() for text in texts)
                )

    def test_original_source_survives_sqlite_restart_without_a_refetch_or_body_rewrite(
        self,
    ):
        item = originals()[-1]
        harness = SocialHarness(wish(WishId.FACT, "fact"))
        play_content(harness, item)
        harness.finish()
        with tempfile.TemporaryDirectory(prefix="aiko-plaudern-social-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), harness.pet, PetSettings())
            loaded = SqliteStateStore(path).load_session(now=WALL).state
            original = loaded.moodlets.active[0].causes[0].social_content
            self.assertEqual(original, item.evidence)
            text = " ".join(b.content for b in talk(loaded).beats if b.kind == "text")
            self.assertIn("…«", text)
            self.assertEqual(
                loaded.moodlets.active[0].causes[0].social_content, original
            )

    def test_friendship_and_feeling_change_framing_without_changing_the_quoted_source(
        self,
    ):
        item = originals()[2]
        harness = SocialHarness(wish(WishId.TWO_PARTS, "twopart"))
        play_content(harness, item)
        harness.finish()
        cause = harness.pet.moodlets.active[0].causes[0]
        frames = set()
        for stage in FriendshipStage:
            for emotion in (
                EmotionalState.CALM,
                EmotionalState.DOWNCAST,
                EmotionalState.AMBIVALENT,
            ):
                reaction = choose_social(self.book, cause, stage=stage, emotion=emotion)
                quotes = [
                    b.content for b in reaction.beats if b.content.startswith("»")
                ]
                self.assertEqual(
                    quotes, [f"»{p}«" for p in require_test_value(item.evidence).parts]
                )
                frames.add(reaction.line_id)
                if emotion != EmotionalState.CALM:
                    self.assertIn(
                        "mixed" if emotion == EmotionalState.AMBIVALENT else "quiet",
                        reaction.line_id,
                    )
        self.assertGreaterEqual(len(frames), 4)

    def test_older_category_only_causes_do_not_invent_a_fact_or_punchline(self):
        for category in ("single", "twopart", "fact"):
            harness = SocialHarness(wish(WishId(category), category))
            completion = require_test_value(harness.admit(category))
            harness.player.cancel()
            harness.controller.complete_social(
                replace(completion, content=None),
                harness.inputs,
                arrangement_ready=False,
            )
            cause = harness.pet.moodlets.active[0].causes[0]
            reaction = choose_social(self.book, cause)
            self.assertIn("old-", reaction.line_id)
            self.assertFalse(any(b.content.startswith("»") for b in reaction.beats))

    def test_source_braces_are_literal_and_wide_placeholders_need_their_own_bubble(
        self,
    ):
        payload = fact_payload()
        payload["text"] = "Ein Testfakt mit {Klammern} und einem vollständigen Satz."
        item = prepare_social_content(SocialCategory.FACT, payload)
        harness = SocialHarness(wish(WishId.FACT, "fact"))
        play_content(harness, item)
        harness.finish()
        self.assertIn(
            "{Klammern}", " ".join(b.content for b in talk(harness.pet).beats)
        )
        raw = dict(
            id="bad-reference",
            event="talk",
            animation="idle",
            periods=[],
            weekdays=[],
            presentation="story",
        )
        for topic, text in (
            ("social.fact", "{source_quote}"),
            ("social.content.fact", "Fakt: {source_quote}"),
            ("social.content.two_part", "{source_quote}"),
        ):
            with self.subTest(topic=topic), self.assertRaises(ValueError):
                Line.parse(
                    dict(
                        raw,
                        conditions=[dict(conversation_topics=[topic])],
                        beats=[dict(kind="text", content=text)],
                    )
                )


if __name__ == "__main__":
    unittest.main()
