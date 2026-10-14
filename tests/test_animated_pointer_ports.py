"""The sprite accepts the desktop pointer sampler without duplicating input."""

import unittest
from unittest.mock import Mock

from aiko_pet.ui.pet_view.animated_pet import AnimatedPorts


class AnimatedPointerPortsTests(unittest.TestCase):
    def test_optional_pointer_sample_retains_existing_ports(self) -> None:
        ports = AnimatedPorts(
            track=Mock(), toolbar_visible=Mock(), place_x=Mock(),
            action_until=Mock(), action_state=Mock(),
            walk_finished=Mock(), cursor_moved=Mock(), extend_action=Mock(),
        )
        self.assertIsNone(ports.pointer_sample)

    def test_injected_sampler_is_kept_by_the_port(self) -> None:
        def sample() -> tuple[int, int, int]:
            return 10, 20, 1920

        ports = AnimatedPorts(
            track=Mock(), toolbar_visible=Mock(), place_x=Mock(),
            action_until=Mock(), action_state=Mock(),
            walk_finished=Mock(), cursor_moved=Mock(), extend_action=Mock(),
            pointer_sample=sample,
        )
        assert ports.pointer_sample is not None
        self.assertEqual(ports.pointer_sample(), (10, 20, 1920))
