"""Late World callbacks read one typed runtime without fabricated state."""

import unittest
from types import SimpleNamespace
from typing import cast

from aiko_pet.desktop.world_access import WorldRuntimeAccess
from aiko_pet.desktop.world_runtime import DesktopWorldRuntime


class WorldRuntimeAccessTests(unittest.TestCase):
    def test_unbound_reads_are_safe_and_bound_reads_follow_live_owner(self):
        access = WorldRuntimeAccess()
        self.assertFalse(access.focused())
        self.assertFalse(access.defer_routine())
        episode = SimpleNamespace(active=False, focus_record=None)
        stub = cast(DesktopWorldRuntime, SimpleNamespace(
            interaction=episode, user_action_pending=False,
        ))
        access.bind(stub)
        self.assertFalse(access.focused())
        self.assertFalse(access.defer_routine())
        episode.focus_record = "memory_1"
        self.assertTrue(access.focused())
        episode.active = True
        self.assertTrue(access.defer_routine())
        episode.active = False
        stub.user_action_pending = True
        self.assertTrue(access.defer_routine())
        with self.assertRaises(RuntimeError):
            access.bind(stub)
