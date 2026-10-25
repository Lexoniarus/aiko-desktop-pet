"""Concrete game storytelling preserves original goals and real result evidence."""

import random
import unittest
from dataclasses import replace
from itertools import product

from test_conversation_topics import actual
from test_plaudern import mastermind_win, talk
from test_rps_result_evidence import finish_actual_round
from test_wish_assignment import wish
from test_wish_game_assignment import coordinator, pet_with

from aiko_pet.games.contracts import (
    BlackjackDecisionReason,
    BlackjackDetails,
    RockPaperScissorsDetails,
    RockPaperScissorsMove,
)
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.conversation_topics import ConversationKind, ConversationTopic
from aiko_pet.pet.mind.dialogue_context import FriendshipStage
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletCauseKind,
    MoodletGameResult,
    MoodletId,
    MoodletOutcome,
    MoodletWishCause,
)
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.wishes import WishId
from tools.dialogue_test_support import dialogue_context
from tools.pet_test_support import require_test_value

TIME = context_at(1800000000)


def source(target, outcome="win", *, objective=None, count=1, final=None, details=None):
    definition = {
        "next_win": "win_round",
        "retry_win": "comeback_game",
        "next_non_loss": "avoid_round_loss",
        "total_rounds": "play_game",
        "session_rounds": "play_game",
        "total_wins": "win_overall",
        "block_majority": "win_overall",
        "block_non_loss": "avoid_overall_loss",
    }.get(objective or "", "play_game")
    return replace(
        actual(target=target),
        attribution=MoodletAttribution.USER,
        kind=MoodletCauseKind.WISH_FULFILLED
        if objective
        else MoodletCauseKind.INTERACTION,
        outcome=MoodletOutcome(outcome),
        game_details=details,
        wish=None
        if objective is None
        else MoodletWishCause(
            1,
            definition,
            target,
            objective,
            count,
        ),
        game=None
        if final is None
        else MoodletGameResult(
            MoodletOutcome(final),
            count + 2,
            count,
            1,
        ),
    )


def choose_game(
    book, cause, *, stage=FriendshipStage.FRIEND, emotion=EmotionalState.CALM
):
    context = replace(
        dialogue_context(TIME, stage=stage),
        emotions=EmotionalComposition(emotion),
        conversation_topic=ConversationTopic(
            ConversationKind.GAME,
            1,
            MoodletId.SHARED_PLAY,
            cause,
        ),
    )
    reaction = require_test_value(
        book.choose("talk", context, 10, presentation="story")
    )
    return reaction, " ".join(b.content for b in reaction.beats if b.kind == "text")


class PlaudernGameTests(unittest.TestCase):
    def setUp(self):
        self.book = DialogueBook.from_file(rng=random.Random(0))

    def test_all_revealed_rps_pairs_render_only_the_actual_hands(self):
        names = {"rock": "Stein", "paper": "Papier", "scissors": "Schere"}
        for player, aiko in product(RockPaperScissorsMove, repeat=2):
            details = RockPaperScissorsDetails(player, aiko)
            cause = source("rock_paper_scissors", details.aiko_outcome, details=details)
            with self.subTest(player=player, aiko=aiko):
                reaction, text = choose_game(self.book, cause)
                self.assertIn(names[player.value], text)
                self.assertIn(names[aiko.value], text)
                self.assertIn("rps-hands-", reaction.line_id)
                self.assertNotIn("{", text)
        pet = pet_with(wish(WishId.WIN_ROUND, "rock_paper_scissors"))
        finish_actual_round(
            coordinator(pet),
            1,
            RockPaperScissorsMove.SCISSORS,
            RockPaperScissorsMove.ROCK,
        )
        self.assertIn("Stein", talk(pet).text)
        self.assertIn("Schere", talk(pet).text)

    def test_blackjack_naturals_comparisons_and_later_21_are_distinct(self):
        reason = BlackjackDecisionReason
        cases = (
            BlackjackDetails(18, 26, reason.AIKO_BUST),
            BlackjackDetails(27, 5, reason.PLAYER_BUST),
            BlackjackDetails(18, 21, reason.AIKO_BLACKJACK),
            BlackjackDetails(21, 16, reason.PLAYER_BLACKJACK),
            BlackjackDetails(21, 21, reason.BOTH_BLACKJACK),
            BlackjackDetails(18, 20, reason.HIGHER_TOTAL),
            BlackjackDetails(20, 18, reason.HIGHER_TOTAL),
            BlackjackDetails(21, 21, reason.EQUAL_TOTAL),
        )
        for details in cases:
            with self.subTest(details=details):
                reaction, text = choose_game(
                    self.book,
                    source(
                        "blackjack",
                        details.aiko_outcome,
                        details=details,
                    ),
                )
                self.assertTrue(reaction.line_id.startswith("plaudern-blackjack-"))
                self.assertNotIn("{", text)
                if details.reason in (
                    reason.AIKO_BLACKJACK,
                    reason.PLAYER_BLACKJACK,
                    reason.BOTH_BLACKJACK,
                ):
                    self.assertIn("zwei Karten", text)
                else:
                    self.assertNotIn("zwei Karten", text)
        _, legacy = choose_game(self.book, source("blackjack", "loss"))
        self.assertNotIn("21", legacy)
        self.assertNotIn("über", legacy)

    def test_total_wins_keep_count_and_require_final_win_for_a_final_connection(self):
        for final in ("win", "draw", "loss"):
            cause = source("connect_four", objective="total_wins", count=3, final=final)
            reaction, text = choose_game(self.book, cause)
            self.assertIn("3 Siege", text)
            self.assertNotIn("hintereinander", text)
            self.assertNotIn("in Folge", text)
            if final == "win":
                self.assertIn("Viererreihe", text)
            else:
                self.assertNotIn("Viererreihe", text)
                self.assertNotIn("goal-wins-connect_four", reaction.line_id)

    def test_play_goals_majority_and_nonloss_are_not_rewritten_as_total_wins(self):
        for objective, outcome, expected in (
            ("total_rounds", "completed", "Spielrunden"),
            ("session_rounds", "completed", "Spielrunden"),
            ("block_majority", "win", "vorne"),
            ("block_non_loss", "draw", "nicht"),
        ):
            _, text = choose_game(
                self.book,
                source(
                    "mastermind",
                    outcome,
                    objective=objective,
                    count=3,
                    final="draw",
                ),
            )
            self.assertIn(expected, text)
            self.assertNotIn("ungeknackt", text)
            self.assertNotIn("3 Siege", text)
        failed = replace(
            source(
                "blackjack", "loss", objective="block_non_loss", count=3, final="draw"
            ),
            kind=MoodletCauseKind.WISH_FAILED,
        )
        self.assertIn("insgesamt hinten", choose_game(self.book, failed)[1])

    def test_original_nonloss_draw_and_quiz_do_not_become_a_victory(self):
        cause = source("tic_tac_toe", "draw", objective="next_non_loss")
        _, text = choose_game(self.book, cause)
        self.assertIn("Dreierreihe", text)
        self.assertIn("nicht verlieren", text)
        _, quiz = choose_game(self.book, source("quiz", "completed"))
        self.assertIn("Quiz", quiz)
        self.assertNotIn("gewonnen", quiz)
        self.assertNotIn("besiegt", quiz)

    def test_friendship_and_mixed_or_quiet_feeling_preserve_the_same_result(self):
        pet = mastermind_win()
        cause = pet.moodlets.active[0].causes[0]
        variants = set()
        for stage in FriendshipStage:
            for emotion in (
                EmotionalState.CALM,
                EmotionalState.DOWNCAST,
                EmotionalState.AMBIVALENT,
            ):
                reaction, text = choose_game(
                    self.book, cause, stage=stage, emotion=emotion
                )
                self.assertIn("Mastermind-Code", text)
                self.assertTrue("ungeknackt" in text or "nicht geknackt" in text)
                variants.add(reaction.line_id)
        self.assertGreater(len(variants), 2)

    def test_new_goal_filters_reject_unknown_vocabulary(self):
        raw = dict(
            id="invalid",
            event="talk",
            animation="idle",
            presentation="story",
            periods=[],
            weekdays=[],
            beats=[dict(kind="text", content="Hallo.")],
        )
        for field in (
            "conversation_targets",
            "conversation_objectives",
            "conversation_outcomes",
            "conversation_round_outcomes",
            "conversation_wishes",
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                Line.parse(
                    dict(
                        raw,
                        conditions=[
                            dict(
                                conversation_topics=["game.cumulative"],
                                **{field: ["invented"]},
                            )
                        ],
                    )
                )


if __name__ == "__main__":
    unittest.main()
