"""The sprite receives immutable attention and never samples OS pointers."""

import unittest
from unittest.mock import Mock

from aiko_pet.pet.mind.cursor_attention import CursorAttentionSnapshot
from aiko_pet.ui.pet_view.animated_pet import AnimatedPorts


class AnimatedPointerPortsTests(unittest.TestCase):
    def test_sprite_ports_are_only_renderer_and_movement_callbacks(self) -> None:
        ports = AnimatedPorts(
            track=Mock(), toolbar_visible=Mock(), place_x=Mock(),
            action_until=Mock(), action_state=Mock(),
            walk_finished=Mock(), extend_action=Mock(),
        )
        self.assertFalse(hasattr(ports, "pointer_sample"))
        self.assertFalse(hasattr(ports, "cursor_moved"))

    def test_snapshots_preserve_readonly_timing_values(self) -> None:
        value = CursorAttentionSnapshot(5.0, 6.0)
        self.assertEqual((value.last_pointer_move, value.attention_until),
                         (5.0, 6.0))
