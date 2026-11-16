"""Real portable-session boundaries, using isolated saves and explicit time."""

import json
import math
import tempfile
import unittest
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.browser.bootstrap import create_browser_session
from aiko_pet.frontend.games.room_effects import RoomGameEffects
from aiko_pet.frontend.room_locomotion import ROOM_WALK_ANIMATION, RoomLocomotion
from aiko_pet.frontend.room_movement import RoomMovement
from aiko_pet.world.room import RoomGeometry, RoomPoint
from aiko_pet.world.room_navigation import RoomLeg, RoomNavigator
from tools.pet_test_support import set_test_pet_values


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
        self.assertEqual(snapshot["animation"], ROOM_WALK_ANIMATION)
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

    def test_call_stays_on_the_same_bearing_at_all_friendship_levels(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        session = self.endpoint.session
        room = session.room
        start = RoomPoint(*room.geometry.polar_position(-0.61, 220))
        target = RoomPoint(*room.geometry.polar_position(-0.61, 180))
        for friendship in (40, 50, 60):
            with self.subTest(friendship=friendship):
                set_test_pet_values(session.state, friendship=friendship)
                room.world.locate_in_room(replace(room.spatial, pet=start))
                reply = self.command(
                    "call", x=target.x, depth=target.depth, wall="north"
                )
                call_id = reply["snapshot"]["call_id"]
                self.assertIsNotNone(call_id)
                initial = room.movement.distance_walked
                self.advance_until(lambda: room.position == target)
                self.assertEqual(room.movement.points, (target,))
                self.assertAlmostEqual(room.movement.distance_walked - initial, 40)
                self.wall += 0.25
                standing = self.command("tick")["snapshot"]
                self.assertEqual(standing["animation"], "rest-neutral")
                self.assertEqual(standing["call_id"], call_id)

    def test_rejected_call_does_not_arm_a_later_movement(self) -> None:
        room = self.endpoint.session.room
        nearby = RoomPoint(*room.geometry.polar_position(-0.61, 145))
        with self.assertRaisesRegex(ValueError, "Ungültige Blickrichtung"):
            room.call(nearby, wall="invalid")
        room.world.locate_in_room(replace(room.spatial, pet=nearby))
        self.assertIsNone(self.command("snapshot")["snapshot"]["call_id"])

    def test_deferred_call_gets_an_identity_only_when_its_route_starts(self) -> None:
        room = self.endpoint.session.room
        deferred: list[Callable[[], None]] = []
        with patch.object(room.interaction, "interrupt", side_effect=deferred.append):
            reply = self.command("call", x=470, depth=100)
        self.assertIsNone(reply["snapshot"]["call_id"])
        deferred[0]()
        active = self.command("snapshot")["snapshot"]["call_id"]
        self.assertIsNotNone(active)

        cancelled = self.command("suspend")["snapshot"]
        self.assertIsNone(cancelled["call_id"])
        self.command("resume")
        second = self.command("call", x=470, depth=100)["snapshot"]["call_id"]
        self.assertNotEqual(second, active)

    def test_near_call_reaches_radius_70_without_restarting_on_repeat(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        bearing = 0.35
        start = RoomPoint(*room.geometry.polar_position(bearing, 200))
        transition = RoomPoint(*room.geometry.polar_position(bearing, 131))
        target = RoomPoint(*room.geometry.polar_position(bearing, 70))
        room.world.locate_in_room(replace(room.spatial, pet=start))
        first = self.command("call", bearing=bearing)["snapshot"]
        call_id = first["close_call_id"]
        self.assertIsNotNone(call_id)
        self.advance_until(lambda: room.position != start)
        serial = room.movement.serial
        again = self.command("call", bearing=bearing)["snapshot"]
        self.assertEqual(again["close_call_id"], call_id)
        self.assertEqual(room.movement.serial, serial)
        self.advance_until(lambda: room.position == target)
        first_stop, final_stop = room.movement.points
        self.assertAlmostEqual(room.geometry.distance(first_stop, transition), 0)
        self.assertEqual(final_stop, target)
        self.assertAlmostEqual(room.movement.distance_walked, 130)

        self.command("call", bearing=bearing)
        self.wall += 0.5
        standing = self.command("tick")["snapshot"]
        self.assertEqual(standing["close_call_id"], call_id)
        self.assertEqual(standing["animation"], "rest-neutral")
        self.assertFalse(standing["moving"])
        self.assertEqual(room.movement.serial, serial)

    def test_blocked_near_call_stops_at_the_transition(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        layout = room.geometry.layout
        table = next(item for item in layout.furniture if item.id == "table")
        obstacle = replace(table, id="test_obstacle", x=400, z=200, width=4, depth=4)
        geometry = replace(room.geometry, layout=replace(
            layout, furniture=(*layout.furniture, obstacle)
        ))
        room.geometry = geometry
        room.movement = RoomMovement(RoomNavigator(geometry))
        start, transition, target = (RoomPoint(400, z) for z in (90, 169, 230))
        self.assertTrue(geometry.layout.can_place(
            target.x, target.depth, geometry.layout.pet_radius, minimum_distance=70,
        ))
        room.world.locate_in_room(replace(room.spatial, pet=start))
        self.command("call", bearing=0)
        self.advance_until(lambda: room.position == transition)
        self.assertEqual(room.movement.points, (transition,))

    def test_near_position_reopens_and_exits_along_the_arrival_ray(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        bearing = 0.35
        close = RoomPoint(*room.geometry.polar_position(bearing, 70))
        transition = RoomPoint(*room.geometry.polar_position(bearing, 131))
        room.world.locate_in_room(replace(room.spatial, pet=close))
        self.command("suspend")
        self.endpoint = create_browser_session(str(self.path))
        self.sequence = 0
        reopened = self.endpoint.session.room
        self.assertEqual(reopened.position, close)
        self.assertFalse(reopened.geometry.layout.can_place(
            close.x, close.depth, reopened.geometry.layout.pet_radius
        ))
        self.command("call", x=470, depth=100)
        self.advance_until(lambda: reopened.position == RoomPoint(470, 100))
        self.assertAlmostEqual(
            reopened.geometry.distance(reopened.movement.points[0], transition), 0
        )

    def test_table_game_walks_out_of_the_near_position_before_starting(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        session = self.endpoint.session
        room = session.room
        close, transition = RoomPoint(400, 230), RoomPoint(400, 169)
        room.world.locate_in_room(replace(room.spatial, pet=close))
        reply = self.command("game_open", id="connect_four")["snapshot"]
        self.assertTrue(reply["game"]["preparing"])
        self.assertEqual(room.position, close)
        self.assertIsNone(session.games.sequence)
        self.advance_until(lambda: session.games.sequence is not None)
        self.assertEqual(room.movement.points[0], transition)
        self.assertEqual(room.position, RoomPoint(675, 396.25))

    def test_motion_snapshot_carries_the_duration_used_by_the_simulation(self) -> None:
        locomotion = self.endpoint.session.room.locomotion
        locomotion.step_duration = 0.4
        motion = self.command("snapshot")["snapshot"]["motion"]
        self.assertEqual(motion["step_duration"], 0.4)
        self.assertAlmostEqual(
            locomotion.speed * motion["step_duration"], motion["step_length"]
        )

    def test_apple_route_crosses_the_wall_joint_at_constant_depth(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        geometry = room.geometry
        joint = math.atan2(geometry.layout.width, geometry.layout.depth)
        left, right = joint - 0.095, joint + 0.095
        far, near = 225, 145
        route = ((left, far), (right, far), (right, near), (left, near))
        positions = [
            RoomPoint(*geometry.polar_position(angle, distance))
            for angle, distance in route
        ]
        room.world.locate_in_room(replace(room.spatial, pet=positions[0]))
        apple = RoomPoint(*geometry.polar_position(joint, 190))
        reply = self.command("place", definition="apple", x=apple.x, depth=apple.depth)
        snapshot = reply["snapshot"]
        placed = next(
            obj for obj in snapshot["objects"] if obj["definition_id"] == "apple"
        )
        depths = dict(snapshot["room"]["object_depths"])
        actual = RoomPoint(placed["position"]["x"], depths[placed["instance_id"]])
        apple_angle, apple_distance = geometry.polar(actual)
        self.assertAlmostEqual(apple_angle, joint)
        self.assertLess(near, apple_distance)
        self.assertLess(apple_distance, far)

        lengths = (far * (right - left), far - near, near * (right - left))
        for target, side, length in zip(
            positions[1:], (1, 0, -1), lengths, strict=True,
        ):
            self.command("call", x=target.x, depth=target.depth)
            initial = room.movement.distance_walked
            previous = room.position
            walked = 0
            while previous != target and walked < 40:
                self.wall += 0.25
                snapshot = self.command("tick")["snapshot"]
                walked += 1
                if room.position != previous:
                    leg = RoomLeg.between(geometry, previous, room.position)
                    assert leg is not None
                    self.assertEqual(leg.side, side)
                    self.assertTrue(
                        room.movement.navigator.clear_segment(previous, room.position)
                    )
                    self.assertEqual(snapshot["animation"], ROOM_WALK_ANIMATION)
                    expected_step = room.locomotion.speed * 0.25
                    if room.position == target:
                        self.assertLessEqual(leg.length, expected_step + 1e-8)
                    else:
                        self.assertAlmostEqual(leg.length, expected_step)
                    previous = room.position
            self.assertEqual(room.position, target)
            self.assertAlmostEqual(room.movement.distance_walked - initial, length)

    def test_called_route_goes_around_table_on_free_floor(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        start = RoomPoint(540, 300)
        goal = RoomPoint(740, 300)
        room.world.locate_in_room(replace(room.spatial, pet=start))
        self.command("call", x=goal.x, depth=goal.depth)
        self.advance_until(lambda: room.position == goal)
        route = (start, *room.movement.points)
        self.assertGreater(len(route), 2)
        for first, last in zip(route, route[1:]):
            self.assertTrue(room.movement.navigator.clear_segment(first, last))

    def test_table_game_walks_around_furniture_before_starting(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        start = RoomPoint(540, 300)
        room.world.locate_in_room(replace(room.spatial, pet=start))
        self.command("place", definition="apple", x=470, depth=100)
        objects = room.world.snapshot().objects
        reply = self.command("game_open", id="connect_four")["snapshot"]
        self.assertTrue(reply["game"]["preparing"])
        self.assertEqual(room.position, start)
        self.assertIsNone(self.endpoint.session.games.sequence)
        for _ in range(180):
            self.wall += 0.25
            self.command("tick")
            self.assertTrue(room.geometry.layout.can_place(
                room.position.x, room.position.depth, room.geometry.layout.pet_radius,
            ))
            if self.endpoint.session.games.sequence is not None:
                break
        self.assertEqual(room.position, RoomPoint(675, 396.25))
        self.assertIsNotNone(self.endpoint.session.games.sequence)
        self.command("game_close")
        self.command("suspend")
        reopened = create_browser_session(str(self.path))
        self.assertEqual(reopened.session.room.position, room.position)
        self.assertEqual(reopened.session.room.world.snapshot().objects, objects)

    def test_cancelled_table_walk_never_starts_a_late_game(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        room = self.endpoint.session.room
        self.command("game_open", id="connect_four")
        self.wall += 0.25
        self.command("tick")
        reply = self.command("game_close")["snapshot"]
        stopped = room.position
        for _ in range(12):
            self.wall += 0.25
            reply = self.command("tick")["snapshot"]
        self.assertIsNone(reply["game"])
        self.assertEqual(room.position, stopped)
        self.command("game_open", id="connect_four")
        self.command("suspend")
        reopened = create_browser_session(str(self.path))
        self.assertIsNone(reopened.session.snapshot()["game"])

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

    def test_ground_food_requires_front_contact_before_pickup(self) -> None:
        self.command("settings", auto_walk=False, spontaneous_talk=False,
                     auto_routine=False)
        session = self.endpoint.session
        session.state.restore_checkpoint(
            replace(session.state.capture_checkpoint(), satiety=10)
        )
        room = session.room
        point = room.geometry.food_placement(RoomPoint(250, 100))
        room.world.locate_in_room(replace(room.spatial, pet=RoomPoint(239.2, 85.6)))
        instance = self.command("place", definition="apple", x=point.x,
                                depth=point.depth)["snapshot"]["objects"][0]["instance_id"]
        original = room.world.get(instance).position
        self.assertFalse(room.environment.at_pickup_contact(point))
        self.advance_until(lambda: room.interaction.phase == "pick_up")
        self.assertEqual(room.position, room.environment.approach_target(point))
        self.assertLess(room.geometry.distance(room.position, RoomPoint(400, 300)),
                        room.geometry.distance(point, RoomPoint(400, 300)))
        self.assertEqual(room.world.get(instance).state.value, "resting")
        self.assertEqual(room.world.get(instance).position, original)
        self.assertIsNone(room.held_item)
        self.advance_until(lambda: room.world.get(instance).state.value == "pet_held")
        self.assertEqual(room.held_item, "apple")
        self.advance_until(lambda: room.world.get(instance).state.value == "consumed")
        self.command("suspend")
        reopened = create_browser_session(str(self.path))
        self.assertEqual(reopened.session.room.world.snapshot().objects, ())
        self.assertGreater(reopened.session.state.satiety, 10)

    def test_pickup_stations_keep_the_front_free_on_all_walls(self) -> None:
        environment = self.endpoint.session.room.environment
        centre = RoomPoint(400, 300)
        for point in (RoomPoint(250, 100), RoomPoint(700, 180),
                      RoomPoint(400, 500), RoomPoint(100, 200)):
            target = environment.approach_target(point)
            self.assertIsNotNone(target)
            assert target is not None
            self.assertLess(environment.geometry.distance(centre, target),
                            environment.geometry.distance(centre, point))
            self.assertTrue(environment.geometry.layout.can_place(
                target.x, target.depth, environment.geometry.layout.pet_radius))
        self.assertIsNone(environment.approach_target(RoomPoint(400, 180)))

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

    def test_legacy_food_position_survives_reopen_and_drag_cancel(
        self,
    ) -> None:
        original = self.command("place", definition="apple", x=460, depth=100)[
            "snapshot"
        ]["objects"][0]
        room = self.endpoint.session.room
        room.world.move_in_room(
            original["instance_id"], RoomPoint(460, 90), 0,
            expected_revision=original["revision"],
        )
        self.command("suspend")
        self.endpoint = create_browser_session(str(self.path))
        original = self.command("snapshot")["snapshot"]["objects"][0]
        self.assertEqual(original["position"]["x"], 460)
        self.assertEqual(self.endpoint.session.room.spatial.depth_for(
            original["instance_id"]), 90)
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
        self.assertEqual(self.endpoint.session.room.spatial.depth_for(
            original["instance_id"]), 90)

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
        expected = self.endpoint.session.room.geometry.food_placement(
            RoomPoint(510, 110),
        )
        self.assertAlmostEqual(moved["position"]["x"], expected.x)
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
        self.assertAlmostEqual(reopened.spatial.depth_for(item["instance_id"]),
                               expected.depth)

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

    def test_unaccepted_offers_use_food_line_on_timeout_and_suspend(self) -> None:
        room = self.endpoint.session.room
        expected = room.geometry.food_placement(room.position)
        with patch.object(room.interaction, "offer_on_release", return_value=False):
            self.command("offer", definition="apple")
            self.advance_until(
                lambda: room.world.snapshot().objects[0].state.value == "falling",
            )
        first = room.world.snapshot().objects[0]
        assert first.position is not None
        self.assertAlmostEqual(first.position.x, expected.x)
        self.assertAlmostEqual(room.spatial.depth_for(first.instance_id),
                               expected.depth)
        self.command("offer", definition="cookie")
        self.command("suspend")
        reopened = create_browser_session(str(self.path)).session.room
        second = reopened.world.snapshot().objects[1]
        assert second.position is not None
        self.assertEqual(second.state.value, "resting")
        self.assertAlmostEqual(second.position.x, expected.x)
        self.assertAlmostEqual(reopened.spatial.depth_for(second.instance_id),
                               expected.depth)

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
            (ready["animation"], ready["animation_hold_frame"]), ("hold_item", 0)
        )
        self.command("object_drag_drop", x=400, depth=100, height=25, offer=True)
        self.assertEqual(session.room.world.get(token).state.value, "pet_held")
        self.advance_until(
            lambda: session.room.world.get(token).state.value == "consumed"
        )
        self.assertGreater(session.state.satiety, 30)

    def _approach_for_near_handover(self) -> None:
        session = self.endpoint.session
        session.state.restore_checkpoint(
            replace(session.state.capture_checkpoint(), satiety=30)
        )
        self.command("settings", spontaneous_talk=False, auto_walk=False)
        self.command("call", bearing=0)
        self.advance_until(
            lambda: session.room.position == RoomPoint(400, 230)
            and not session.room.moving
        )

    def _move_to_near_handover(self) -> None:
        self.command(
            "object_drag_move",
            x=415, depth=230, height=90, inside=True, near_handover=True,
        )

    def _feed_at_near_handover(self, *, wait_for_ready: bool) -> None:
        self._approach_for_near_handover()
        session = self.endpoint.session
        room = session.room
        self.command("object_drag_start", definition="onigiri")
        token = room.drag_instance
        assert token is not None
        self._move_to_near_handover()
        held = room.world.get(token)
        assert held.position is not None
        self.assertEqual((held.position.x, held.position.height), (400, 40))
        self.assertEqual(room.spatial.depth_for(token), 230)
        if wait_for_ready:
            self.advance_until(lambda: room.drag_ready)
        self.assertLessEqual(session.state.satiety, 30)
        self.command(
            "object_drag_drop", x=415, depth=230, height=90,
            offer=True, near_handover=True,
        )
        self.assertEqual(
            room.world.get(token).state.value,
            "pet_held" if wait_for_ready else "user_held",
        )
        self.advance_until(lambda: room.world.get(token).state.value == "pet_held")
        self.advance_until(lambda: room.world.get(token).state.value == "consumed")
        self.assertGreater(session.state.satiety, 30)
        self.assertEqual([item.instance_id for item in room.world.snapshot().objects],
                         [token])

    def test_near_handover_continues_observing_a_quick_release(self) -> None:
        self._feed_at_near_handover(wait_for_ready=False)

    def test_near_handover_accepts_a_ready_portion_on_release(self) -> None:
        self._feed_at_near_handover(wait_for_ready=True)

    def test_leaving_near_handover_uses_the_floor_and_cancel_restores_the_item(
        self,
    ) -> None:
        self._approach_for_near_handover()
        room = self.endpoint.session.room
        self.command("object_drag_start", definition="apple")
        discarded = room.drag_instance
        assert discarded is not None
        self._move_to_near_handover()
        self.command("object_drag_cancel")
        self.assertEqual(room.world.get(discarded).state.value, "removed")

        placed = self.command("place", definition="apple", x=510, depth=170)
        original = next(
            item for item in placed["snapshot"]["objects"]
            if item["state"] == "resting"
        )
        token = original["instance_id"]
        original_depth = room.spatial.depth_for(token)
        self.command("object_drag_start", instance=token, revision=original["revision"])
        self._move_to_near_handover()
        self.command("object_drag_cancel")
        restored = room.world.get(token)
        assert restored.position is not None
        self.assertEqual(restored.state.value, "resting")
        self.assertEqual(restored.position.x, original["position"]["x"])
        self.assertEqual(room.spatial.depth_for(token), original_depth)
        self.command("object_drag_start", instance=token, revision=restored.revision)
        self._move_to_near_handover()
        self.command("object_drag_move", x=570, depth=240, height=45, inside=True)
        self.command("object_drag_drop", x=570, depth=240, height=45, offer=False)
        released = room.world.get(token)
        assert released.position is not None
        floor = room.geometry.food_placement(RoomPoint(570, 240))
        self.assertEqual(
            (released.state.value, released.position.height), ("falling", 45)
        )
        self.assertAlmostEqual(released.position.x, floor.x)
        self.assertAlmostEqual(room.spatial.depth_for(token), floor.depth)

    def test_unaccepted_near_handover_falls_on_the_food_line(self) -> None:
        self._approach_for_near_handover()
        room = self.endpoint.session.room
        self.command("object_drag_start", definition="apple")
        token = room.drag_instance
        assert token is not None
        self._move_to_near_handover()
        with patch.object(room.interaction, "offer_on_release", return_value=False):
            self.command("object_drag_drop", x=400, depth=230, offer=True,
                         near_handover=True)
            self.advance_until(lambda: room.world.get(token).state.value == "falling")
        floor = room.geometry.food_placement(room.position)
        self.assertAlmostEqual(room.spatial.depth_for(token), floor.depth)

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
                    "args": {"definition": "horoscope_book", "x": 610, "depth": 300},
                })
            )
        )
        self.assertFalse(rejected["ok"])
        self.assertEqual(session.room.world.snapshot().objects, before.objects)
        item = self.command("place", definition="horoscope_book", x=550, depth=300)[
            "snapshot"]["objects"][0]
        self.assertEqual(item["position"]["x"], 550)
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
                self.assertEqual(current["animation"], ROOM_WALK_ANIMATION)
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
    def test_clear_route_uses_one_bend_and_keeps_exact_coordinates(self) -> None:
        from aiko_pet.infrastructure.room_layout import load_room_layout
        from aiko_pet.world.room_navigation import RoomNavigator

        navigator = RoomNavigator(RoomGeometry(load_room_layout()))
        start = RoomPoint(409.5, 161.25)
        goal = RoomPoint(533.75, 303.5)
        route = navigator.find_route(start, goal)
        assert route is not None
        self.assertEqual((route.points[0], route.points[-1]), (start, goal))
        self.assertEqual(len(route.points), 3)
        for first, last in zip(route.points, route.points[1:]):
            self.assertTrue(navigator.clear_segment(first, last))

    def test_off_centre_radial_route_stays_a_single_segment(self) -> None:
        from aiko_pet.infrastructure.room_layout import load_room_layout
        from aiko_pet.world.room_navigation import RoomNavigator

        geometry = RoomGeometry(load_room_layout())
        navigator = RoomNavigator(geometry)
        start = RoomPoint(*geometry.polar_position(-0.61, 250))
        goal = RoomPoint(*geometry.polar_position(-0.61, 195))
        route = navigator.find_route(start, goal)
        assert route is not None
        self.assertEqual(route.points, (start, goal))

    def test_routes_go_around_the_table_without_cutting_its_corners(self) -> None:
        from aiko_pet.infrastructure.room_layout import load_room_layout
        from aiko_pet.world.room_navigation import RoomNavigator

        geometry = RoomGeometry(load_room_layout())
        navigator = RoomNavigator(geometry)
        route = navigator.find_route(RoomPoint(540, 300), RoomPoint(740, 300))
        self.assertIsNotNone(route)
        assert route is not None
        self.assertGreater(len(route.points), 2)
        for start, end in zip(route.points, route.points[1:]):
            self.assertTrue(navigator.clear_segment(start, end))
        self.assertIsNone(
            navigator.find_route(RoomPoint(540, 300), RoomPoint(610, 300))
        )

    def test_room_walk_continues_through_each_corner_and_can_stop(self) -> None:
        pose = RoomLocomotion()
        self.assertFalse(pose.walk(0, 1))
        self.assertTrue(pose.selection.animation.startswith("body-orient-"))
        for step in range(1, 9):
            pose.walk(step * 0.1, 1)
        for side in (1, 0, -1, 0):
            self.assertTrue(pose.walk(0.9, side))
            self.assertEqual(pose.selection.animation, ROOM_WALK_ANIMATION)
        pose.stop_walk()
        self.assertEqual(pose.selection.animation, "rest-neutral")
        self.assertTrue(pose.walk(1, 0))
        self.assertEqual(pose.selection.animation, ROOM_WALK_ANIMATION)

    def test_room_rest_can_hold_a_quarter_pose_after_a_walk(self) -> None:
        pose = RoomLocomotion()
        for step in range(10):
            pose.walk(step * 0.1, 1)
        pose.rest(2, (1, 0))
        self.assertEqual(
            (pose.selection.animation, pose.selection.fixed_frame),
            ("body-look-right", 4),
        )
