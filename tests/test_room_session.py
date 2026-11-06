"""Real portable-session boundaries, using isolated saves and explicit time."""

import json
import tempfile
import unittest
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.browser.bootstrap import create_browser_session
from aiko_pet.frontend.games.room_effects import RoomGameEffects
from aiko_pet.frontend.room_locomotion import RoomLocomotion
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
                    "protocol": 2,
                    "requestId": self.sequence,
                    "name": name,
                    "args": args,
                })
            )
        )
        self.assertTrue(result["ok"], result.get("error"))
        return result

    def advance_until(self, complete: Callable[[], bool]) -> None:
        shown = -1
        for _ in range(180):
            self.wall += 0.25
            reply = self.command("tick")["snapshot"]
            speech = reply["speech"]
            if speech["text"] and speech["id"] != shown:
                shown = speech["id"]
                self.command("speech_ack", id=shown)
            if complete():
                return
        self.fail("Room interaction did not reach its semantic boundary")

    def test_accepted_call_moves_the_world_and_persists_across_reopen(self) -> None:
        before = self.endpoint.session.room.position
        self.command("call", x=470, depth=100)
        snapshot = self.command("snapshot")["snapshot"]
        for _ in range(12):
            self.wall += 0.25
            snapshot = self.command("tick")["snapshot"]
        self.assertEqual(snapshot["animation"], "body-step-right-profil")
        position = self.endpoint.session.room.position
        self.assertLess(
            RoomGeometry.distance(position, RoomPoint(470, 100)),
            RoomGeometry.distance(before, RoomPoint(470, 100)),
        )
        self.command("suspend")
        reopened = create_browser_session(str(self.path))
        self.assertEqual(reopened.session.room.position, position)
        self.assertFalse(reopened.session.settings.learn_rhythm)
        self.assertFalse(reopened.session.settings.observe_computer)

    def test_called_route_goes_around_table_on_free_floor(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        room.world.locate_in_room(replace(room.spatial, pet=RoomPoint(610, 300)))
        self.command("call", x=740, depth=300)
        for _ in range(180):
            self.wall += 0.25
            self.command("tick")
            self.assertTrue(room.geometry.layout.can_place(
                room.position.x, room.position.depth, room.geometry.layout.pet_radius,
            ))
            if room.position == RoomPoint(740, 300):
                break
        self.assertEqual(room.position, RoomPoint(740, 300))

    def test_duplicate_request_cannot_create_a_second_portion(self) -> None:
        message = json.dumps({
            "protocol": 2,
            "requestId": 900,
            "name": "place",
            "args": {"definition": "apple", "x": 460, "depth": 100},
        })
        first = self.endpoint.dispatch_json(message)
        self.assertTrue(json.loads(first)["ok"])
        self.assertEqual(self.endpoint.dispatch_json(message), first)
        self.assertEqual(len(self.endpoint.session.room.world.snapshot().objects), 1)

    def test_unknown_transport_command_is_rejected_without_changing_state(self) -> None:
        before = self.endpoint.session.state.capture_checkpoint()
        reply = self.endpoint.dispatch_json(
            json.dumps({
                "protocol": 2,
                "requestId": 12,
                "name": "eval",
                "args": {},
            })
        )
        self.assertFalse(json.loads(reply)["ok"])
        self.assertEqual(self.endpoint.session.state.capture_checkpoint(), before)

    def test_search_forecast_uses_copies_of_all_live_owners(self) -> None:
        session = self.endpoint.session
        self.command("place", definition="onigiri", x=460, depth=100)
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
        self.command("call", x=430, depth=100)
        self.command("offer", definition="onigiri")
        self.advance_until(
            lambda: any(
                item.state.value == "consumed"
                for item in session.room.world.snapshot().objects
            )
        )
        self.assertGreater(session.state.satiety, 30)
        self.assertEqual(
            sum(
                item.state.value == "consumed"
                for item in session.room.world.snapshot().objects
            ),
            1,
        )

    def test_offered_book_starts_local_reading_and_reuses_its_identity(self) -> None:
        self.command("settings", zodiac_sign="leo", auto_routine=False)
        self.command("call", x=430, depth=100)
        self.command("horoscope")
        session = self.endpoint.session
        self.advance_until(lambda: session.playback.snapshot().story)
        self.assertIsNotNone(session.content)
        assert session.content is not None
        day = session.content.horoscope.today()
        self.assertIsNotNone(day)
        self.command("suspend")
        self.command("resume")
        self.command("horoscope")
        self.assertEqual(
            len([
                item
                for item in session.room.world.snapshot().objects
                if item.definition_id == "horoscope_book"
            ]),
            1,
        )

    def test_drag_cancel_restores_the_same_portion(
        self,
    ) -> None:
        original = self.command("place", definition="apple", x=460, depth=100)[
            "snapshot"
        ]["objects"][0]
        self.command(
            "object_drag_start",
            instance=original["instance_id"],
            revision=original["revision"],
        )
        held = self.command("snapshot")["snapshot"]["objects"][0]
        self.assertEqual(held["state"], "user_held")
        restored = self.command("object_drag_cancel")["snapshot"]["objects"]
        self.assertEqual(len(restored), 1)
        self.assertEqual(restored[0]["instance_id"], original["instance_id"])
        self.assertEqual(restored[0]["position"], original["position"])
        self.assertEqual(restored[0]["state"], "resting")

    def test_drag_drop_and_suspension_keep_world_identity_and_depth(self) -> None:
        item = self.command("place", definition="apple", x=460, depth=100)["snapshot"][
            "objects"
        ][0]
        self.command(
            "object_drag_start", instance=item["instance_id"], revision=item["revision"]
        )
        moved = self.command("object_drag_drop", x=510, depth=110, offer=False)[
            "snapshot"
        ]["objects"][0]
        self.assertEqual(moved["instance_id"], item["instance_id"])
        self.assertEqual(moved["position"]["x"], 510)
        self.assertEqual(moved["state"], "falling")
        self.advance_until(
            lambda: self.endpoint.session.room.world.get(
                item["instance_id"]
            ).state.value
            == "resting"
        )
        moved = self.command("snapshot")["snapshot"]["objects"][0]
        self.command(
            "object_drag_start",
            instance=moved["instance_id"],
            revision=moved["revision"],
        )
        self.command("suspend")
        reopened = create_browser_session(str(self.path)).session.room
        self.assertEqual(reopened.world.get(item["instance_id"]).state.value, "resting")
        self.assertEqual(reopened.spatial.depth_for(item["instance_id"]), 110)

    def test_air_release_uses_world_fall_and_cancel_creates_no_supply(self) -> None:
        self.command("object_drag_start", definition="apple")
        self.command("object_drag_move", x=470, depth=110, height=70, inside=True)
        released = self.command(
            "object_drag_drop", x=470, depth=110, height=70, offer=False
        )["snapshot"]["objects"][0]
        self.assertEqual(
            (released["state"], released["position"]["height"]), ("falling", 70)
        )
        self.wall += 0.1
        falling = self.command("tick")["snapshot"]["objects"][0]
        self.assertGreater(falling["position"]["height"], 0)
        self.assertLess(falling["position"]["height"], 70)
        self.advance_until(
            lambda: self.endpoint.session.room.world.get(
                released["instance_id"]
            ).state.value
            == "resting"
        )
        self.command("object_drag_start", definition="onigiri")
        self.command("object_drag_cancel")
        objects = self.command("snapshot")["snapshot"]["objects"]
        self.assertEqual(
            [
                o["instance_id"]
                for o in objects
                if o["state"] not in ("removed", "consumed")
            ],
            [released["instance_id"]],
        )

    def test_face_presentation_recognizes_before_release_and_eats_only_after_handover(
        self,
    ) -> None:
        session = self.endpoint.session
        session.state.restore_checkpoint(
            replace(session.state.capture_checkpoint(), satiety=30)
        )
        self.command("settings", spontaneous_talk=False, auto_walk=False)
        self.command("object_drag_start", definition="onigiri")
        token = session.room.drag_instance
        assert token is not None
        self.command(
            "object_drag_move",
            x=400,
            depth=100,
            height=60,
            inside=True,
            face_x=0,
            face_y=0,
        )
        self.advance_until(
            lambda: bool(
                (known := session.room.awareness.known_instance(token)) is not None
                and known.recognized
            )
        )
        self.assertEqual(session.room.world.get(token).state.value, "user_held")
        self.assertLess(session.state.satiety, 31)
        self.command(
            "object_drag_move",
            x=400,
            depth=100,
            height=25,
            inside=True,
            face_x=0,
            face_y=0.28,
        )
        self.wall += 0.1
        ready = self.command("tick")["snapshot"]
        self.assertTrue(ready["drag"]["ready"])
        self.assertEqual(
            (ready["animation"], ready["animation_hold_frame"]), ("pick_up", 7)
        )
        self.command("object_drag_drop", x=400, depth=100, height=25, offer=True)
        self.assertEqual(session.room.world.get(token).state.value, "pet_held")
        self.advance_until(
            lambda: session.room.world.get(token).state.value == "consumed"
        )
        self.assertGreater(session.state.satiety, 30)

    def test_furniture_footprints_reject_drop_but_allow_free_ground_in_front(
        self,
    ) -> None:
        session = self.endpoint.session
        before = session.room.world.snapshot()
        rejected = json.loads(
            self.endpoint.dispatch_json(
                json.dumps({
                    "protocol": 2,
                    "requestId": 500,
                    "name": "place",
                    "args": {"definition": "apple", "x": 665, "depth": 300},
                })
            )
        )
        self.assertFalse(rejected["ok"])
        self.assertEqual(session.room.world.snapshot().objects, before.objects)
        item = self.command("place", definition="apple", x=600, depth=300)["snapshot"][
            "objects"
        ][0]
        self.assertEqual(item["position"]["x"], 600)
        self.assertEqual(session.room.spatial.depth_for(item["instance_id"]), 300)

    def test_room_effects_never_expose_a_dealt_hole_card(self) -> None:
        self.command("game_open", id="blackjack")

        def hole_in_flight() -> bool:
            game = self.endpoint.session.games.snapshot()
            motion = game["props"]["motion"] if game else None
            return bool(motion and motion["kind"] == "dealer" and motion["index"] == 1)

        self.advance_until(hole_in_flight)
        game = self.endpoint.session.games.snapshot()
        assert game is not None
        self.assertIsNone(game["props"]["motion"]["card"])

    def test_petting_finishes_its_pose_even_when_the_dialogue_was_not_seen(
        self,
    ) -> None:
        self.command(
            "settings", auto_walk=False, spontaneous_talk=False, auto_routine=False
        )
        first = self.command("care", action="pet")["snapshot"]
        self.assertEqual(first["animation"], "petting")
        self.assertTrue(first["speech"]["text"] or first["speech"]["emote"])
        current = first
        for _ in range(40):
            if current["speech"]["text"]:
                break
            self.wall += 0.25
            current = self.command("tick")["snapshot"]
        self.assertTrue(current["speech"]["text"])
        unseen = current["speech"]["id"]
        for _ in range(50):
            self.wall += 0.2
            current = self.command("tick")["snapshot"]
        self.assertNotEqual(current["animation"], "petting")
        self.assertEqual(self.endpoint.session.playback.animation, "idle")
        self.assertTrue(self.endpoint.session.playback.player.active)
        self.assertEqual(current["speech"]["id"], unseen)

    def test_petting_returns_to_a_visible_walk_and_the_finished_route_stays_put(
        self,
    ) -> None:
        self.command(
            "settings", auto_walk=False, spontaneous_talk=False, auto_routine=False
        )
        self.command("care", action="pet")
        self.advance_until(
            lambda: self.endpoint.session.playback.animation == "idle"
            and not self.endpoint.session.playback.player.active
        )
        current = self.command("call", x=450, depth=100)["snapshot"]
        saw_walk = False
        for _ in range(80):
            self.wall += 0.1
            current = self.command("tick")["snapshot"]
            if current["moving"]:
                saw_walk = True
                self.assertEqual(current["animation"], "body-step-right-profil")
        self.assertTrue(saw_walk)
        self.assertLess(
            RoomGeometry.distance(
                self.endpoint.session.room.position, RoomPoint(450, 100)
            ),
            0.01,
        )
        self.assertFalse(current["moving"])
        current = self.command("call", x=450, depth=100)["snapshot"]
        self.wall += 0.2
        current = self.command("tick")["snapshot"]
        self.assertFalse(current["moving"])
        self.assertFalse(current["animation"].startswith("body-orient-"))

    def test_room_outing_holds_a_quarter_pose_then_yields_to_care(self) -> None:
        session = self.endpoint.session
        self.command(
            "settings", auto_walk=True, spontaneous_talk=False, auto_routine=False
        )
        session.mind.rng.seed(7)
        session.room.leisure.next_outing = session.room.now
        friendship = session.state.friendship
        self.advance_until(lambda: session.room.moving)
        self.advance_until(
            lambda: session.room.locomotion.selection.animation.startswith("body-look-")
        )
        position = session.room.position
        first_frame = session.room.locomotion.selection.fixed_frame
        self.advance_until(
            lambda: session.room.locomotion.selection.fixed_frame != first_frame
        )
        self.assertEqual(session.room.position, position)
        self.assertTrue(
            session.room.locomotion.selection.animation.startswith("body-look-")
        )
        self.assertEqual(session.state.friendship, friendship)
        self.assertFalse(session.room.world.snapshot().objects)
        self.assertEqual(
            self.command("care", action="pet")["snapshot"]["animation"], "petting"
        )
        self.assertFalse(session.room.moving)
        self.assertGreater(session.room.leisure.next_outing, session.room.now)

    def test_cosmetic_snack_has_no_food_effects_and_cancels_cleanly(
        self,
    ) -> None:
        session = self.endpoint.session
        before = session.state.capture_checkpoint()
        completed = []
        effects = RoomGameEffects(session.playback)
        effects.finale(False, lambda: completed.append(True))
        session.playback.advance(20)
        self.assertEqual(completed, [True])
        self.assertIsNone(effects.held_item)
        self.assertEqual(session.state.capture_checkpoint(), before)
        self.assertFalse(session.room.world.snapshot().objects)
        effects.finale(True, lambda: completed.append(False))
        effects.close()
        session.playback.advance(20)
        self.assertEqual(completed, [True])


class RoomGeometryTests(unittest.TestCase):
    def test_routes_go_around_the_table_without_cutting_its_corners(self) -> None:
        from aiko_pet.infrastructure.room_layout import load_room_layout
        from aiko_pet.world.room_navigation import RoomNavigator

        geometry = RoomGeometry(load_room_layout())
        navigator = RoomNavigator(geometry)
        route = navigator.find_route(RoomPoint(610, 300), RoomPoint(740, 300))
        self.assertIsNotNone(route)
        assert route is not None
        self.assertGreater(len(route.points), 2)
        for start, end in zip(route.points, route.points[1:]):
            self.assertTrue(navigator.clear_segment(start, end))
        self.assertIsNone(
            navigator.find_route(RoomPoint(610, 300), RoomPoint(665, 300))
        )

    def test_profile_steps_and_quarter_body_facing_use_distinct_source_banks(
        self,
    ) -> None:
        pose = RoomLocomotion()
        for step in range(10):
            pose.walk(step * 0.1, RoomPoint(600), RoomPoint(900))
        self.assertEqual(pose.selection.animation, "body-step-right-profil")
        pose.rest(2, (1, 0))
        self.assertEqual(
            (pose.selection.animation, pose.selection.fixed_frame),
            ("body-look-right", 4),
        )
        for step in range(10):
            pose.walk(3 + step * 0.1, RoomPoint(600, 100), RoomPoint(600, 130))
        self.assertEqual(pose.selection.animation, "body-step-right-profil")
        for step in range(10):
            pose.walk(4 + step * 0.1, RoomPoint(900), RoomPoint(600))
        self.assertEqual(pose.selection.animation, "body-step-left-profil")
