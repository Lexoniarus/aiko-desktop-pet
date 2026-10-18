"""Activity selects attention; a rendered sprite never establishes visibility."""

import unittest

from aiko_pet.application.object_behavior import choose_object_attention
from aiko_pet.application.object_feedback import InteractionPhase
from aiko_pet.pet.mind.object_attention import ObjectAttention


class ObjectAttentionTests(unittest.TestCase):
    def test_action_and_movement_precedence_over_cursor_and_free_targets(self):
        cases: tuple[tuple[InteractionPhase, float, ObjectAttention], ...] = (
            ("idle", 0, ObjectAttention("cursor", (-2, 1))),
            ("approach", 10, ObjectAttention("object", None)),
            ("search", -10, ObjectAttention("moving", (-1, 0))),
            ("inspect", 10, ObjectAttention("object", None)),
            ("put_down", 0, ObjectAttention("object", None)),
            ("await_return", 0, ObjectAttention("object", (-2, 1), focused_place=True)),
            ("notice", 0, ObjectAttention("object", None)),
        )
        for phase, walking, expected in cases:
            with self.subTest(phase=phase, walking=walking):
                self.assertEqual(choose_object_attention(
                    phase, sleeping=False, game_open=False, walking=walking,
                    cursor=(-2, 1), target=None,
                ), expected)
        for sleeping, game_open in ((True, False), (False, True)):
            self.assertEqual(choose_object_attention(
                "approach", sleeping=sleeping, game_open=game_open, walking=10,
                cursor=(-2, 1), target=(3, 0),
            ), ObjectAttention("unavailable", None))

    def test_idle_without_cursor_and_explicit_targets_remain_distinct(self):
        cases: tuple[tuple[InteractionPhase, tuple[float, float] | None,
                           ObjectAttention], ...] = (
            ("idle", None, ObjectAttention("survey", None)),
            ("idle", (2, 0), ObjectAttention("survey", (2, 0))),
            ("approach", (2, 0), ObjectAttention("object", (2, 0), focused_place=True)),
            ("await_settle", (2, 0),
             ObjectAttention("object", (2, 0), focused_place=True)),
        )
        for phase, target, expected in cases:
            self.assertEqual(choose_object_attention(
                phase, sleeping=False, game_open=False, walking=0,
                cursor=None, target=target,
            ), expected)

    def test_selected_place_survives_grasp_without_opening_hand_surroundings(self):
        for width in (192, 384):
            origin = (100, width * .6)
            pickup = ObjectAttention("object", (0, -.6), origin=origin,
                                     width=width, focused_place=True)
            hand = ObjectAttention("object", (0, -.2), origin=origin, width=width)
            self.assertTrue(pickup.sees(100, 0))
            self.assertFalse(pickup.sees(100 + width, 0))
            self.assertFalse(hand.sees(100, 0))
        cases: tuple[tuple[InteractionPhase, float, str], ...] = (
            ("idle", 0, "cursor"), ("inspect", 0, "object"),
            ("search", 10, "moving"),
        )
        for phase, walking, mode in cases:
            attention = choose_object_attention(
                phase, sleeping=False, game_open=False, walking=walking,
                cursor=(3, 1), target=(-3, 0), following_cursor=True,
            )
            self.assertEqual(attention.mode, mode)
            if mode == "cursor":
                self.assertEqual(attention.direction, (3, 1))

    def test_other_activity_blocks_free_perception_until_complete(self):
        for phase in ("idle", "search"):
            self.assertEqual(choose_object_attention(
                phase, sleeping=False, game_open=False, walking=10,
                cursor=(1, 0), target=(2, 0), following_cursor=True,
                activity_active=True,
            ), ObjectAttention("unavailable", None))
        # An object's own feedback belongs to that same committed interaction.
        attention = choose_object_attention(
            "approach", sleeping=False, game_open=False, walking=10,
            cursor=(-1, 0), target=(2, 0), activity_active=True,
        )
        self.assertEqual(attention, ObjectAttention("object", (2, 0),
                                                    focused_place=True))

    def test_near_field_and_directed_range_in_body_relative_coordinates(self):
        for attention, offset, visible in (
            (ObjectAttention("survey", None), (-.5, -.4), True),
            (ObjectAttention("survey", None), (2, -.4), False),
            (ObjectAttention("moving", (1, 0)), (3, -.4), True),
            (ObjectAttention("moving", (1, 0)), (-3, -.4), False),
            (ObjectAttention("moving", (-1, 0)), (-3, -.4), True),
            (ObjectAttention("moving", (-1, 0)), (3, -.4), False),
            (ObjectAttention("cursor", (0, 2)), (2, 2), True),
            (ObjectAttention("cursor", (0, 2)), (2, -2), False),
            (ObjectAttention("cursor", (0, 0)), (2, 0), False),
            (ObjectAttention("cursor", (1, 0)), (7, 0), False),
            (ObjectAttention("object", (1, 0)), (.1, 0), False),
            (ObjectAttention("unavailable", None), (.1, 0), False),
        ):
            with self.subTest(attention=attention, offset=offset):
                self.assertEqual(attention.sees_environment(*offset), visible)
