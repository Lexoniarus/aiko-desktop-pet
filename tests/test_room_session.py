"""Real portable-session boundaries, using isolated saves and explicit time."""

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.browser.bootstrap import create_browser_session
from aiko_pet.world.room import RoomGeometry, RoomPoint


class RoomSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = self.enterContext(tempfile.TemporaryDirectory())
        self.wall = datetime(2026, 11, 5, 12).timestamp()
        self.enterContext(patch("time.time", side_effect=lambda: self.wall))
        self.enterContext(patch("time.monotonic", return_value=1000.0))
        self.path = Path(self.folder) / "state.sqlite3"
        self.endpoint = create_browser_session(str(self.path))
        self.sequence = 0

    def command(self, name: str, **args: object) -> dict:
        self.sequence += 1
        result = json.loads(
            self.endpoint.dispatch_json(
                json.dumps({
                    "protocol": 1,
                    "requestId": self.sequence,
                    "name": name,
                    "args": args,
                })
            )
        )
        self.assertTrue(result["ok"], result.get("error"))
        return result

    def test_accepted_call_moves_the_world_and_persists_across_reopen(self) -> None:
        before = self.endpoint.session.room.position
        self.command("call", x=900, depth=1.2)
        for _ in range(4):
            self.wall += 0.25
            self.command("tick")
        position = self.endpoint.session.room.position
        self.assertLess(
            RoomGeometry.distance(position, RoomPoint(900, 1.2)),
            RoomGeometry.distance(before, RoomPoint(900, 1.2)),
        )
        self.command("suspend")
        reopened = create_browser_session(str(self.path))
        self.assertEqual(reopened.session.room.position, position)
        self.assertFalse(reopened.session.settings.learn_rhythm)
        self.assertFalse(reopened.session.settings.observe_computer)

    def test_duplicate_request_cannot_create_a_second_portion(self) -> None:
        message = json.dumps({
            "protocol": 1,
            "requestId": 900,
            "name": "place",
            "args": {"definition": "apple", "x": 800, "depth": 1.2},
        })
        first = self.endpoint.dispatch_json(message)
        self.assertTrue(json.loads(first)["ok"])
        self.assertEqual(self.endpoint.dispatch_json(message), first)
        self.assertEqual(len(self.endpoint.session.room.world.snapshot().objects), 1)

    def test_unknown_transport_command_is_rejected_without_changing_state(self) -> None:
        before = self.endpoint.session.state.capture_checkpoint()
        reply = self.endpoint.dispatch_json(
            json.dumps({
                "protocol": 1,
                "requestId": 12,
                "name": "eval",
                "args": {},
            })
        )
        self.assertFalse(json.loads(reply)["ok"])
        self.assertEqual(self.endpoint.session.state.capture_checkpoint(), before)

    def test_search_forecast_uses_copies_of_all_live_owners(self) -> None:
        session = self.endpoint.session
        self.command("place", definition="onigiri", x=800, depth=0.9)
        before = (
            session.state.capture_checkpoint(),
            session.room.world.snapshot(),
            session.room.awareness.memory.snapshot(),
        )
        result = session.forecast()
        self.assertLessEqual(len(result), 3)
        self.assertEqual(
            (
                session.state.capture_checkpoint(),
                session.room.world.snapshot(),
                session.room.awareness.memory.snapshot(),
            ),
            before,
        )

    def test_closing_unplayed_games_grants_no_completion_reward(self) -> None:
        for game in (
            "rock_paper_scissors",
            "tic_tac_toe",
            "blackjack",
            "connect_four",
            "mastermind",
            "quiz",
        ):
            with self.subTest(game=game):
                before = self.endpoint.session.state.fun
                self.command("game_open", id=game)
                self.assertEqual(
                    self.command("snapshot")["snapshot"]["game"]["id"], game
                )
                self.command("game_close")
                self.assertEqual(self.endpoint.session.state.fun, before)
                self.assertIsNone(self.command("snapshot")["snapshot"]["game"])

    def test_unshown_dialogue_cannot_complete_from_elapsed_time(self) -> None:
        self.command("care", action="talk")
        player = self.endpoint.session.playback
        first = player.snapshot()
        self.assertTrue(first.text)
        player.advance(1000)
        self.assertEqual(player.snapshot().id, first.id)
        self.assertTrue(player.player.active)
        player.suspend()
        self.assertFalse(player.player.active)

    def test_offered_food_uses_real_handover_and_consumes_one_portion(self) -> None:
        session = self.endpoint.session
        session.state.restore_checkpoint(
            replace(session.state.capture_checkpoint(), satiety=30)
        )
        self.command("offer", definition="onigiri")
        shown = -1
        for _ in range(180):
            self.wall += 0.25
            reply = self.command("tick")["snapshot"]
            speech = reply["speech"]
            if speech["text"] and speech["id"] != shown:
                shown = speech["id"]
                self.command("speech_ack", id=shown)
            if any(
                item.state.value == "consumed"
                for item in session.room.world.snapshot().objects
            ):
                break
        self.assertGreater(session.state.satiety, 30)
        self.assertEqual(
            sum(
                item.state.value == "consumed"
                for item in session.room.world.snapshot().objects
            ),
            1,
        )
