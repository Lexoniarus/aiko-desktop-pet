"""Carry original provider words through actual playback, without native UI."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from test_social_content import fact_payload, joke_payload
from test_social_sayings import quotation, quote_payload
from test_wish_assignment import wish
from test_wish_social_assignment import WALL, SocialHarness

from aiko_pet.application.commands import CareCommand
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    prepare_social_content,
    with_intro_variant,
)
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.infrastructure.social_history_codec import encode_social_history
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.care_evidence import CareEvidenceState
from aiko_pet.pet.interaction_events import SocialCompletion
from aiko_pet.pet.moodlets import MoodletCauseKind, MoodletId, MoodletState
from aiko_pet.pet.wishes import WishId
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import require_test_value


def originals() -> tuple[PreparedSocialContent, ...]:
    fact = fact_payload()
    fact["text"] = "Ein langer vollständiger Testsatz mit unveränderten Wörtern. " * 4
    return (
        prepare_social_content(SocialCategory.SINGLE,
                               joke_payload(SocialCategory.SINGLE)),
        quotation(quote_payload()),
        prepare_social_content(SocialCategory.TWO_PARTS,
                               joke_payload(SocialCategory.TWO_PARTS)),
        prepare_social_content(SocialCategory.FACT, fact),
    )


def play_content(harness: SocialHarness, content: PreparedSocialContent):
    outcome = harness.controller.execute(
        CareCommand("talk", conversation=content), harness.inputs,
    )
    reaction = require_test_value(outcome.reaction)
    harness.player.play(reaction)
    return require_test_value(reaction.completed_social)


class SocialEvidencePlaybackTests(unittest.TestCase):
    def test_preparation_and_rotation_preserve_original_parts_and_attribution(self):
        for item in originals():
            with self.subTest(kind=require_test_value(item.evidence).kind):
                content = require_test_value(item.evidence)
                self.assertEqual((content.identity, content.fingerprint),
                                 (item.identity, item.fingerprint))
                self.assertEqual(
                    (content.source, content.source_url, content.permalink),
                    (item.source, item.source_url, item.permalink),
                )
                self.assertEqual((content.author, content.author_url,
                                  content.license_name, content.license_url),
                                 (item.author, item.author_url,
                                  item.license_name, item.license_url))
                source_beats = [b.content for b in item.reaction.beats[1:]
                                if b.kind == "text"]
                if content.kind == "quotation":
                    self.assertEqual(content.parts, (quote_payload()["quote"],))
                    self.assertEqual(len(source_beats), 2)  # Includes separate credit.
                elif content.kind == "two_part":
                    self.assertEqual(content.parts, ("Eine Testfrage?",
                                                     "Eine Testantwort."))
                elif content.kind == "fact":
                    self.assertGreater(len(source_beats), 1)
                    self.assertEqual(content.parts, (" ".join(source_beats),))
                else:
                    self.assertEqual(content.parts, (source_beats[0],))
                for variant in range(3):
                    rotated = with_intro_variant(item, variant)
                    self.assertIs(rotated.evidence, content)
                    self.assertEqual(rotated.reaction.beats[1:],
                                     item.reaction.beats[1:])

    def test_complete_formats_reach_assigned_wish_cause_and_sqlite_restart_once(self):
        with tempfile.TemporaryDirectory(prefix="aiko-social-playback-") as folder:
            for index, item in enumerate(originals()):
                with self.subTest(category=item.category, provider=item.provider):
                    harness = SocialHarness(wish(WishId(item.category), item.category))
                    completion = play_content(harness, item)
                    self.assertIs(completion.content, item.evidence)
                    self.assertTrue(harness.pet.wishes.active)
                    self.assertFalse(harness.pet.moodlets.active)
                    harness.finish()
                    self.assertFalse(harness.pet.wishes.active)
                    cause = harness.pet.moodlets.active[0].causes[0]
                    self.assertEqual(cause.kind, MoodletCauseKind.WISH_FULFILLED)
                    self.assertIs(cause.social_content, item.evidence)
                    self.assertEqual(require_test_value(cause.wish).instance_id, 1)
                    history = SocialContentHistory().admitted(SocialContentReceipt(
                        item.category, item.identity, item.fingerprint,
                        item.intro_variant,
                    ))
                    self.assertEqual(set(encode_social_history(history)["entries"][0]),
                                     {"category", "identity", "fingerprint",
                                      "intro_variant"})
                    path = Path(folder) / f"{index}.sqlite3"
                    save_test_session(
                        SqliteStateStore(path), harness.pet, PetSettings(),
                        social_history=history,
                    )
                    loaded = SqliteStateStore(path).load_session(now=WALL)
                    self.assertEqual(loaded.state.moodlets, harness.pet.moodlets)
                    self.assertEqual(loaded.social_history, history)
                    checkpoint = loaded.state.capture_checkpoint()
                    loaded.state.complete_social_experience(completion)
                    self.assertEqual(loaded.state.capture_checkpoint(), checkpoint)
                    with closing(sqlite3.connect(path)) as connection:
                        columns = {row[1] for row in connection.execute(
                            "PRAGMA table_info(social_receipts)"
                        )}
                        self.assertEqual(columns, {"position_index", "state_id",
                                                   "category", "identity",
                                                   "fingerprint", "intro_variant"})

    def test_interrupted_setup_and_stale_callback_never_store_original_content(self):
        item = originals()[2]
        harness = SocialHarness(wish(WishId.TWO_PARTS, "twopart"))
        play_content(harness, item)
        harness.scheduler.fire(require_test_value(harness.player.pending_timer))
        stale = harness.scheduler.callbacks[
            require_test_value(harness.player.pending_timer)
        ][1]
        harness.player.cancel()
        stale()
        self.assertFalse(harness.pet.moodlets.active)
        self.assertTrue(harness.pet.wishes.active)
        self.assertIsNone(harness.pet.moodlets.care_evidence)
        with tempfile.TemporaryDirectory(prefix="aiko-social-abort-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), harness.pet, PetSettings())
            self.assertFalse(SqliteStateStore(path).load_session(now=WALL).state
                             .moodlets.active)
            with closing(sqlite3.connect(path)) as connection:
                self.assertEqual(connection.execute(
                    "SELECT COUNT(*) FROM moodlet_causes"
                ).fetchone()[0], 0)

    def test_social_gap_retains_content_without_duplicate_wish_award(self):
        for has_wish in (False, True):
            harness = SocialHarness(*([wish(WishId.SOCIAL_ANY)] if has_wish else []))
            harness.pet._change(
                lived_seconds=14400,
                moodlets=MoodletState(care_evidence=CareEvidenceState(0)),
            )
            if has_wish:
                active = replace(harness.pet.wishes.active[0], pinned=True)
                harness.pet._change(wishes=replace(
                    harness.pet.wishes, active=(active,),
                ))
            item = originals()[-1]
            play_content(harness, item)
            harness.finish()
            self.assertEqual(len(harness.pet.moodlets.active), 1)
            episode = harness.pet.moodlets.active[0]
            self.assertEqual(episode.definition_id, MoodletId.CONNECTION)
            self.assertEqual(len(episode.causes), 1)
            self.assertEqual(episode.causes[0].kind, (
                MoodletCauseKind.WISH_FULFILLED if has_wish else
                MoodletCauseKind.INTERACTION
            ))
            self.assertEqual(episode.causes[0].social_content, item.evidence)
            self.assertFalse(any(
                hasattr(event, "social_content") for event in
                require_test_value(harness.pet.moodlets.care_evidence).experiences
            ))

    def test_chat_and_older_missing_originals_stay_valid_without_inventing_text(self):
        harness = SocialHarness(wish(WishId.CHAT, "chat"))
        self.assertIsNone(require_test_value(harness.admit()).content)
        harness.finish()
        self.assertIsNone(harness.pet.moodlets.active[0].causes[0].social_content)
        no_wish = SocialHarness()
        play_content(no_wish, originals()[0])
        no_wish.finish()
        self.assertFalse(no_wish.pet.moodlets.active)
        self.assertEqual(len(require_test_value(
            no_wish.pet.moodlets.care_evidence,
        ).experiences), 1)
        for category, sequence in (("chat", "actual"), ("single", None)):
            with self.assertRaises(ValueError):
                SocialCompletion(category, sequence_id=sequence,
                                 started_at=100 if sequence else None,
                                 content=originals()[0].evidence)


if __name__ == "__main__":
    unittest.main()
