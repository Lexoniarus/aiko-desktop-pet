"""Real room speech/game selections, expression lifetimes and action isolation."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.browser.bootstrap import create_browser_session
from aiko_pet.frontend.room_communication import communication_reaction
from aiko_pet.games.contracts import GameId
from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.pet.animation.expression import EXPRESSION_CLIPS, Expression
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue


class RoomCommunicationTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch("time.time", return_value=datetime(
            2026, 11, 10, 12,
        ).timestamp()))
        self.enterContext(patch("time.monotonic", return_value=1000.0))
        endpoint = create_browser_session(str(Path(folder) / "test.sqlite3"))
        self.session = endpoint.session
        self.session.settings.auto_walk = False
        self.session.settings.auto_routine = False
        self.session.settings.spontaneous_talk = False
        self.session.room.locomotion.rest(0)
        self.addCleanup(self.session.playback.suspend)
        self.addCleanup(self.session.games.close)

    def test_old_speech_gestures_keep_the_selected_v3_emotion_and_return_to_idle(
        self,
    ) -> None:
        player = self.session.playback
        for animation, expression in (
            ("waiting", Expression.WORRIED),
            ("waving", Expression.DOWNCAST),
            ("waving-greeting", Expression.POSITIVE),
            ("jumping", Expression.POSITIVE),
            ("failed", Expression.FIRM),
            ("review", Expression.QUESTIONING),
        ):
            with self.subTest(animation=animation):
                reaction = Reaction(
                    "test", (Cue.text("Ich sehe mich ein wenig um."),),
                    animation, "quiet_alone", expression=expression,
                )
                player.speak(reaction, require_presentation=False)
                self.assertEqual(player.animation, "idle")
                self.assertEqual(
                    self.session.snapshot()["animation"], EXPRESSION_CLIPS[expression],
                )
                self.assertEqual(reaction.animation, animation)
                player.advance(30)
                self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")
                self.assertIsNone(player.expression)

    def test_missing_waiting_intent_stays_neutral_and_text_is_not_lost(self) -> None:
        player = self.session.playback
        player.speak(Reaction.spoken(
            "quiet", "Ich habe Zeit für eine kleine Runde über meinen Platz.",
            "waiting", "quiet_alone",
        ), require_presentation=False)
        self.assertEqual(player.expression, Expression.NEUTRAL)
        self.assertEqual(player.animation, "idle")
        self.assertIn("kleine Runde", player.snapshot().text)

    def test_expression_starts_at_its_authored_beat_and_cancel_clears_it(self) -> None:
        player = self.session.playback
        player.speak(Reaction(
            "timed", (Cue("emote", "question", 500), Cue.text("Was ist da los?")),
            "waiting", "quiet_alone", expression=Expression.QUESTIONING,
            expression_at=1,
        ), require_presentation=False)
        self.assertIsNone(player.expression)
        self.assertEqual(player.animation, "idle")
        player.advance(.5)
        self.assertEqual(player.expression, Expression.QUESTIONING)
        player.player.cancel()
        self.assertIsNone(player.expression)
        player.advance(30)
        self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")

    def test_real_petting_is_not_cancelled_by_a_communication_reaction(self) -> None:
        player = self.session.playback
        player.start_action("petting", 1.0)
        action = player.action_id
        player.speak(Reaction(
            "contact", (Cue.text("Ganz sanft, bitte."),), "waiting", "pet",
            expression=Expression.WORRIED,
        ), require_presentation=False)
        self.assertEqual(player.animation, "petting")
        self.assertEqual(player.action_id, action)
        self.assertIsNone(player.expression)
        player.advance(30)
        self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")

    def test_rps_greeting_has_v3_expression_and_no_stuck_v2_end_pose(self) -> None:
        self.session.games.open(GameId.ROCK_PAPER_SCISSORS)
        self.assertEqual(self.session.snapshot()["animation"], "expression-positive")
        self.assertEqual(self.session.playback.animation, "idle")
        self.session.playback.advance(10)
        self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")

    def test_rps_outcomes_preserve_hand_action_then_show_the_matching_v3_face(
        self,
    ) -> None:
        for move, expression in (
            (Move.SCISSORS, Expression.POSITIVE),
            (Move.PAPER, Expression.DOWNCAST),
            (Move.ROCK, Expression.QUESTIONING),
        ):
            with self.subTest(move=move):
                self.session.games.open(GameId.ROCK_PAPER_SCISSORS)
                flow = self.session.games.sequence
                flow._game._random_index = lambda _size: 0
                flow.choose(move)
                seen = set()
                for _ in range(240):
                    self.session.playback.advance(.05)
                    seen.add(self.session.snapshot()["animation"])
                self.assertIn("attack", seen)
                self.assertIn(EXPRESSION_CLIPS[expression], seen)
                self.assertFalse(seen & {"jumping", "waving", "waiting"})
                self.assertEqual(self.session.playback.animation, "idle")
                self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")
                self.assertEqual(flow.score.games, 1)
                self.session.games.close()

    def test_close_game_clears_its_expression_and_old_timer_cannot_clear_new_one(
        self,
    ) -> None:
        player = self.session.playback
        self.session.games.open(GameId.ROCK_PAPER_SCISSORS)
        stale = [callback for _, callback in player._timers.values()]
        self.session.games.close()
        self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")
        player.express(Expression.WORRIED)
        for callback in stale:
            callback()
        self.assertEqual(player.expression, Expression.WORRIED)

    def test_tic_tac_toe_aiko_win_uses_the_positive_face_instead_of_v2_jumping(
        self,
    ) -> None:
        self.session.games.open(GameId.TIC_TAC_TOE)
        flow = self.session.games.sequence
        for cell, mark in ((0, "X"), (3, "O"), (1, "X"), (4, "O")):
            flow.game.play(cell, mark)
        flow.choose(8)
        flow.advance()
        self.assertEqual(flow.game.board.winner, "O")
        self.assertEqual(self.session.playback.animation, "idle")
        self.assertEqual(self.session.snapshot()["animation"], "expression-positive")
        self.session.playback.advance(30)
        self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")
        self.assertEqual(flow.game.score.games, 1)

    def test_connect_four_win_keeps_the_throw_then_returns_through_v3_to_idle(
        self,
    ) -> None:
        self.session.games.open(GameId.CONNECT_FOUR)
        flow = self.session.games.sequence
        for column in (0, 2, 0, 3, 1, 4):
            flow.game.play(column, flow.game.board.turn)
        flow.choose(0)
        seen = set()
        for _ in range(400):
            self.session.playback.advance(.05)
            seen.add(self.session.snapshot()["animation"])
        self.assertEqual(flow.game.board.winner, 2)
        self.assertIn("throw_item", seen)
        self.assertIn("expression-positive", seen)
        self.assertNotIn("jumping", seen)
        self.assertEqual(self.session.snapshot()["animation"], "rest-neutral")
        self.assertEqual(flow.game.score.games, 1)

    def test_repeated_expression_has_a_new_presentation_id_not_a_new_action(
        self,
    ) -> None:
        player = self.session.playback
        action = player.action_id
        player.express(Expression.POSITIVE)
        first = self.session.snapshot()["animation_id"]
        player.advance(.2)
        player.express(Expression.POSITIVE)
        self.assertNotEqual(first, self.session.snapshot()["animation_id"])
        self.assertEqual(player.action_id, action)

    def test_physical_reactions_and_none_are_not_rewritten(self) -> None:
        self.assertIsNone(communication_reaction(None))
        for name in ("eat", "petting", "pick_up", "put_down", "attack", "idle"):
            with self.subTest(name=name):
                reaction = Reaction.spoken("physical", "Okay.", name, "pet")
                self.assertIs(communication_reaction(reaction), reaction)
