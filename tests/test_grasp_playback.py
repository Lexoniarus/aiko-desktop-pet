"""World custody and readable feedback share the reviewed grasp presentation."""

import unittest

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.frontend.games.room_effects import RoomGameEffects
from aiko_pet.frontend.room_playback import RoomPlayback
from aiko_pet.games.connect_four import Move
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from tests import test_object_interaction as fixture


class GraspInspectionTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.ObjectInteractionTests("runTest")
        self.f.setUp()
        self.f.coordinator._animated_inspection = True
        self.hints = []
        self.f.coordinator._inspection_hint = lambda: self.hints.append(True)
        self.f.start_investigation()
        self.f.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.f.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(self.f.actions[-1], "inspect_item")

    def event(self, clip, now, events=(), finished=False, index=0):
        self.f.stamp = now
        self.f.coordinator.receive(PlaybackEvent(
            len(self.f.actions), clip, index, events, finished,
        ))

    def test_long_comment_extends_only_right_pause_before_recognition(self):
        self.f.delay_feedback = True
        self.assertNotIn("object_inspect", [c.event for c in self.f.cues])
        self.event("inspect_item", .4, ("inspect_comment",), index=1)
        self.event("inspect_item", .4, ("inspect_comment",), index=1)
        self.assertEqual([c.event for c in self.f.cues].count("object_inspect"), 1)
        self.event("inspect_item", .85, ("inspect_emote",), index=2)
        self.assertEqual(self.hints, [True])
        self.event("inspect_item", 2.55, finished=True)
        self.assertEqual(self.f.actions[-1], "inspect_hold")
        self.event("inspect_hold", 3.55, finished=True)
        self.f.stamp = 5
        self.f.coordinator.update()
        self.assertEqual(self.f.actions[-1], "inspect_hold")
        self.assertEqual(self.f.consumed, [])
        self.assertNotIn("object_recognized", [c.event for c in self.f.cues])
        self.f.acknowledge()
        self.assertEqual(self.f.actions[-1], "inspect_return")
        self.event("inspect_return", 5.45, finished=True)
        self.assertEqual(self.f.coordinator.phase, "recognize")
        self.assertEqual(self.f.actions[-1], "hold_item")
        self.assertEqual(self.f.consumed, [])

    def test_short_comment_does_not_skip_either_side_or_return(self):
        self.event("inspect_item", .4, ("inspect_comment",), index=1)
        self.event("inspect_item", 2.55, finished=True)
        self.assertEqual(self.f.actions[-1], "inspect_hold")
        self.event("inspect_hold", 3.55, finished=True)
        self.assertEqual(self.f.actions[-1], "inspect_return")
        self.assertEqual(self.f.consumed, [])
        self.event("inspect_return", 4, finished=True)
        self.assertIn("object_recognized", [c.event for c in self.f.cues])
        self.assertEqual(len(self.f.consumed), 1)

    def test_cancelled_inspection_cannot_deliver_late_hint_or_result(self):
        old = len(self.f.actions)
        self.f.coordinator.interrupt(lambda: None)
        self.assertEqual(self.f.coordinator.phase, "put_down")
        state = self.f.world.snapshot()
        for events in (("inspect_emote",), ("inspect_comment",)):
            self.f.coordinator.receive(PlaybackEvent(old, "inspect_item", 5, events))
        self.f.coordinator.receive(PlaybackEvent(old, "inspect_item", 9, finished=True))
        self.assertEqual(self.hints, [])
        self.assertEqual(self.f.world.snapshot(), state)
        self.assertNotIn("object_recognized", [c.event for c in self.f.cues])


class GraspRoomPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.player = RoomPlayback(load_character_catalog(),
                                   social_completed=lambda _: None,
                                   mark_spoken=lambda: None)
        self.addCleanup(self.player.suspend)

    def test_hint_coexists_with_comment_and_cancel_clears_it(self):
        self.player.comment("Von der Seite erkenne ich vielleicht mehr.", 5000)
        self.player.inspection_hint()
        self.assertEqual(self.player.snapshot().accent, "🔎")
        self.assertTrue(self.player.snapshot().text)
        self.player.advance(.65)
        self.assertEqual(self.player.snapshot().accent, "")
        self.assertTrue(self.player.snapshot().text)
        self.player.inspection_hint()
        self.player.stop_animation()
        self.assertEqual(self.player.snapshot().accent, "")

    def test_pack_markers_use_real_frame_clock_and_hold_uses_one_frame(self):
        events = []
        self.player.receive = events.append
        self.player.play_animation("inspect_item")
        self.player.advance(.399)
        self.assertFalse(any("inspect_comment" in e.events for e in events))
        self.player.advance(.002)
        self.assertEqual(sum("inspect_comment" in e.events for e in events), 1)
        self.player.advance(.45)
        self.assertEqual(sum("inspect_emote" in e.events for e in events), 1)
        self.player.advance(2)
        self.assertEqual(sum(e.finished for e in events), 1)
        self.player.play_animation("hold_item")
        self.assertEqual(self.player.animation, "hold_item")
        self.assertEqual(self.player.hold_frame, 0)

    def test_put_down_releases_at_authored_marker_not_old_source_two(self):
        events = []
        self.player.receive = events.append
        self.player.play_animation("put_down")
        self.player.advance(10)
        release = [e for e in events if "detach_object" in e.events]
        self.assertEqual(len(release), 1)
        self.assertNotEqual(release[0].source_index, 2)

    def test_four_wins_uses_semantic_release_and_last_palm_position(self):
        effects = RoomGameEffects(self.player)
        self.addCleanup(effects.close)
        done = []
        effects.throw(Move(35, 2, False), lambda: done.append(True))
        clip = self.player.clip("throw_item")
        elapsed = 0
        markers = {}
        for frame in clip.frames:
            for event in frame.events:
                markers[event] = elapsed / 1000
            elapsed += frame.duration_ms
        attach_at, release_at = markers["attach_object"], markers["release_object"]
        self.player.advance(attach_at + .001)
        self.assertEqual(effects.held_item, "c4-red")
        self.assertIsNone(effects.snapshot()["motion"])
        self.player.advance(release_at - self.player.now - .001)
        self.assertEqual(effects.held_item, "c4-red")
        self.player.advance(.002)
        self.assertIsNone(effects.held_item)
        motion = effects.snapshot()["motion"]
        self.assertEqual(motion["hand_anchor"], (96, 136))
        self.assertEqual(motion["cell"], 35)
        self.player.advance(5)
        self.assertEqual(done, [True])
        self.assertIsNone(effects.snapshot()["motion"])

    def test_closed_four_wins_cannot_release_or_finish_late(self):
        effects = RoomGameEffects(self.player)
        done = []
        effects.throw(Move(35, 2, False), lambda: done.append(True))
        self.player.advance(.5)
        effects.close()
        self.player.advance(20)
        self.assertEqual(done, [])
        self.assertIsNone(effects.held_item)
        self.assertIsNone(effects.snapshot()["motion"])

    def test_real_room_clock_holds_right_until_comment_finishes(self):
        f = fixture.ObjectInteractionTests("runTest")
        f.setUp()
        f.coordinator._animated_inspection = True
        f.coordinator._play = self.player.play_animation
        f.coordinator._stop = self.player.stop_animation
        f.coordinator._inspection_hint = self.player.inspection_hint
        self.player.receive = f.coordinator.receive
        spoken_at = []

        def feedback(cue):
            if cue.event == "object_inspect":
                spoken_at.append(f.stamp)
                self.player.speak(
                    Reaction("test", (
                        Cue("text", "Ich schaue mir das noch etwas genauer an.", 5000),
                    ), "idle", cue.event),
                    animate=False, require_presentation=False,
                    completed=lambda done: f.coordinator.receive_feedback(
                        FeedbackReceipt(cue.key, done),
                    ),
                )
            else:
                f.coordinator.receive_feedback(FeedbackReceipt(cue.key, True))

        f.coordinator._feedback = feedback
        f.start_investigation()

        def advance(seconds):
            for _ in range(round(seconds / .05)):
                f.stamp += .05
                self.player.advance(.05)
                f.coordinator.update()

        advance(2.5)
        self.assertEqual(self.player.snapshot().accent, "🔎")
        self.assertTrue(self.player.snapshot().text)
        advance(3.5)
        self.assertEqual(self.player.animation, "inspect_hold")
        self.assertEqual(f.consumed, [])
        advance(3)
        self.assertEqual(len(spoken_at), 1)
        self.assertEqual(len(f.consumed), 1)
