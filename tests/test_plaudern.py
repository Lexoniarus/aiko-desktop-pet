"""Requested personal chat derives facts from Pet, without native UI or history."""

import json
import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_blackjack import arranged_game, card
from test_blackjack_result_evidence import finish_blackjack
from test_conversation_topics import actual, episode
from test_wish_assignment import wish
from test_wish_game_assignment import INPUTS, WALL, coordinator, pet_with
from test_wish_social_assignment import SocialHarness

from aiko_pet.application.settings import PetSettings
from aiko_pet.games.contracts import (
    BlackjackDecisionReason,
    BlackjackDetails,
    GameId,
    GameRoundEvent,
)
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook, Line
from aiko_pet.pet.mind.conversation_topics import ConversationKind, ConversationTopic
from aiko_pet.pet.moodlets import MoodletId, MoodletOutcome, MoodletState
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import WishId, WishState
from tools.dialogue_test_support import dialogue_context
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import require_test_value


def mastermind_win():
    pet = pet_with(wish(WishId.WIN_ROUND, "mastermind"))
    runtime = coordinator(pet)
    start = GameRoundEvent(GameId.MASTERMIND, "actual", 1)
    runtime.observe_round(start, INPUTS)
    runtime.observe_round(replace(start, outcome="loss"), INPUTS)
    return pet


def talk(pet, *, context=None):
    mind = make_aiko_mind(rng=random.Random(0), started_at=0)
    return require_test_value(mind.select_reaction(
        "talk", pet, context_at(WALL), 10, dialogue=context,
    ))


class PlaudernTests(unittest.TestCase):
    def test_original_mastermind_result_is_personal_across_friendship_and_emotion(self):
        pet = mastermind_win()
        original = pet.moodlets.active[0].causes[0]
        texts = set()
        for points in (0, 30, 60, 90):
            pet._change(friendship=points)
            reaction = talk(pet)
            text = " ".join(c.content for c in reaction.beats if c.kind == "text")
            self.assertIn("Mastermind-Code", text)
            self.assertNotIn("Wunsch erfüllt", text)
            texts.add(text)
            self.assertEqual(pet.moodlets.active[0].causes[0], original)
        self.assertEqual(len(texts), 4)
        snapshot = make_aiko_mind(started_at=0).dialogue_context(
            pet, context_at(WALL), 10,
        )
        mixed = talk(pet, context=replace(
            snapshot, emotions=EmotionalComposition(EmotionalState.AMBIVALENT),
        ))
        self.assertIn("mixed", mixed.line_id)
        self.assertIn("ungeknackt", mixed.text)

    def test_settled_blackjack_totals_are_rendered_from_the_actual_cause(self):
        pet = pet_with(wish(WishId.AVOID_ROUND_LOSS, "blackjack"))
        # Player stands at 18; Aiko draws at 16 and busts with 26.
        finish_blackjack(coordinator(pet), arranged_game(
            card("10"), card("9"), card("8"), card("7"), card("K"),
        ))
        reaction = talk(pet)
        self.assertTrue(reaction.line_id.startswith("plaudern-blackjack-aiko-bust"))
        self.assertIn("26", reaction.text)
        self.assertNotIn("{", reaction.text)

    def test_intake_and_handover_stay_distinct_with_concrete_food_names(self):
        for food in DEFAULT_CATALOG.foods:
            for outcome in (MoodletOutcome.INTAKE, MoodletOutcome.HANDOVER):
                cause = replace(actual(target=food), outcome=outcome)
                pet = PetState(moodlets=MoodletState(active=(
                    episode(1, MoodletId.FOOD_FULFILLED, 1, cause),
                )), lived_seconds=100)
                reaction = talk(pet)
                text = " ".join(b.content for b in reaction.beats if b.kind == "text")
                self.assertIn(DEFAULT_CATALOG.foods[food].display_name, text)
                self.assertTrue(reaction.line_id.startswith(
                    f"plaudern-food-{outcome.value}-",
                ))
                if outcome == MoodletOutcome.HANDOVER:
                    self.assertNotIn("gegessen", text)
                    self.assertNotIn("geschmeckt", text)

    def test_unknown_causes_and_objects_do_not_invent_identity_or_blame(self):
        pet = PetState(lived_seconds=100, moodlets=MoodletState(active=(
            episode(1, MoodletId.WITHHELD),
        )))
        self.assertTrue(talk(pet).line_id.startswith("plaudern-state-"))
        pet._change(moodlets=MoodletState(active=(
            episode(1, MoodletId.WITHHELD, 1, actual(target="withheld")),
        )))
        reaction = talk(pet)
        self.assertEqual(reaction.line_id, "plaudern-withheld")
        self.assertIn("Ding", reaction.text)
        self.assertNotIn("Du hast", reaction.text)

    def test_only_previously_disclosed_live_wish_is_repeated_in_present_tense(self):
        desired = replace(wish(WishId.CHAT, "chat"), expressed_at=20)
        pet = PetState(lived_seconds=100, mood=80, friendship=90,
                       wishes=WishState(2, (desired,)))
        reaction = talk(pet)
        self.assertEqual(reaction.line_id, "plaudern-wish")
        self.assertEqual(reaction.beats[1].content,
                         make_aiko_mind(started_at=0).wish_reaction(desired).text)
        for hidden, friendship in ((replace(desired, expressed_at=None), 90),
                                   (desired, 0)):
            pet._change(wishes=WishState(2, (hidden,)), friendship=friendship)
            self.assertTrue(talk(pet).line_id.startswith("plaudern-state-"))

    def test_selecting_and_restart_leave_no_additional_history_and_keep_relevance(self):
        pet = mastermind_win()
        before = pet.capture_checkpoint()
        talk(pet)
        self.assertEqual(pet.capture_checkpoint(), before)
        with tempfile.TemporaryDirectory(prefix="aiko-plaudern-restart-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            loaded = SqliteStateStore(path).load_session(now=WALL).state
            self.assertEqual(loaded.capture_checkpoint(), before)
            self.assertIn("Mastermind-Code", talk(loaded).text)

    def test_existing_chat_completion_still_fulfills_once_after_full_playback(self):
        harness = SocialHarness(wish(WishId.CHAT, "chat"))
        completion = require_test_value(harness.admit("chat"))
        self.assertTrue(harness.pet.wishes.active)
        harness.finish()
        self.assertFalse(harness.pet.wishes.active)
        self.assertEqual(harness.pet.moodlets.active[0].definition_id,
                         MoodletId.CONNECTION)
        checkpoint = harness.pet.capture_checkpoint()
        harness.controller.complete_social(completion, harness.inputs,
                                           arrangement_ready=False)
        self.assertEqual(harness.pet.capture_checkpoint(), checkpoint)

    def test_catalogue_rejects_ungrounded_topics_and_unproved_placeholders(self):
        raw = json.loads((CATALOGUE.parent / "plaudern/state.json").read_text("utf-8"))[
            "lines"
        ][0]
        for condition, content in (
            ({}, "Hallo."), ({"conversation_topics": ["invented"]}, "Hallo."),
            ({"conversation_topics": ["state"]}, "Kartenwert {player_total}."),
            ({"conversation_topics": ["food.handover"]}, "Hallo {unknown}."),
        ):
            changed = dict(raw, conditions=[condition], beats=[dict(kind="text",
                                                                  content=content)])
            with self.subTest(condition=condition), self.assertRaises(ValueError):
                Line.parse(changed)
        book = DialogueBook.from_file()
        self.assertIsNone(book.choose("talk", dialogue_context(context_at(WALL)), 10))
        state = replace(dialogue_context(context_at(WALL)),
                        conversation_topic=ConversationTopic(ConversationKind.STATE))
        self.assertIsNotNone(book.choose("talk", state, 10))

    def test_state_fallback_can_reflect_actual_hunger_without_claiming_an_event(self):
        pet = PetState(satiety=5, mood=80)
        self.assertEqual(talk(pet).line_id, "plaudern-state-hungry")

    def test_shared_play_does_not_invent_a_failed_wish_from_its_last_round_loss(self):
        for target, details in (
            ("mastermind", None),
            ("blackjack", BlackjackDetails(18, 26, BlackjackDecisionReason.AIKO_BUST)),
        ):
            cause = replace(actual(target=target), outcome=MoodletOutcome.LOSS,
                            game_details=details)
            pet = PetState(lived_seconds=100, moodlets=MoodletState(active=(
                episode(1, MoodletId.SHARED_PLAY, 1, cause),
            )))
            reaction = talk(pet)
            text = " ".join(b.content for b in reaction.beats if b.kind == "text")
            self.assertNotIn("wollte", text)
            self.assertNotIn("enttäuscht", text)


if __name__ == "__main__":
    unittest.main()
