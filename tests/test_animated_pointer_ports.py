"""The sprite receives immutable attention and never samples OS pointers."""

import unittest
from unittest.mock import Mock

from aiko_pet.pet.mind.cursor_attention import CursorAttentionSnapshot
from aiko_pet.pet.animation.animation import PassiveObservation
from aiko_pet.ui.pet_view.animated_pet import AnimatedPorts


class AnimatedPointerPortsTests(unittest.TestCase):
    def test_sprite_ports_use_movement_events_not_desktop_geometry(self) -> None:
        ports = AnimatedPorts(
            walk_step=Mock(), walk_active=Mock(), interrupt_walk=Mock(),
            observe_passive=Mock(return_value=PassiveObservation(None, False)),
            reset_gaze=Mock(),
            action_until=Mock(), action_state=Mock(), extend_action=Mock(),
        )
        for old_field in ("pointer_sample", "cursor_moved", "track", "place_x"):
            self.assertFalse(hasattr(ports, old_field))

    def test_snapshots_preserve_readonly_timing_values(self) -> None:
        value = CursorAttentionSnapshot(5.0, 6.0)
        self.assertEqual((value.last_pointer_move, value.attention_until),
                         (5.0, 6.0))
