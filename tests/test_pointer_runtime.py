"""Desktop pointer bridge preserves sampling and event dispatch."""

import unittest
from unittest.mock import Mock

from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.desktop.pointer_runtime import PointerRuntime, PointerRuntimePorts
from aiko_pet.pet.mind.cursor_attention import CursorAttention


class PointerRuntimeTests(unittest.TestCase):
    def test_events_are_sent_only_for_changed_pointer(self) -> None:
        attention = CursorAttention()
        on_motion = Mock()
        samples = iter(((10, 20, 1920), (1000, 20, 1920)))
        runtime = PointerRuntime(
            CursorObservation(attention),
            PointerRuntimePorts(
                sample=lambda: next(samples),
                game_mode=lambda: False,
                eyes=lambda: (100, 20),
                on_motion=on_motion,
            ),
        )
        self.assertEqual(runtime.observe(100.0), (10, 20))
        on_motion.assert_not_called()
        self.assertEqual(runtime.observe(101.0), (1000, 20))
        on_motion.assert_called_once_with(900.0, 1920, 101.0)
        self.assertEqual(attention.last_pointer_move, 101.0)
