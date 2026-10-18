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
        self.assertEqual(access.phase(), "idle")
        self.assertFalse(access.following_cursor())
        self.assertIsNone(access.following_record())
        episode = SimpleNamespace(
            active=False, focus_record=None, searching=False, phase="idle",
        )
        awareness = SimpleNamespace(following_cursor=False, following_record=None)
        stub = cast(DesktopWorldRuntime, SimpleNamespace(
            interaction=episode, user_action_pending=False,
            awareness=awareness,
        ))
        access.bind(stub)
        self.assertFalse(access.focused())
        self.assertFalse(access.defer_routine())
        awareness.following_cursor = True
        awareness.following_record = "memory_1"
        self.assertTrue(access.following_cursor())
        self.assertEqual(access.following_record(), "memory_1")
        episode.focus_record = "memory_1"
        episode.phase = "inspect"
        self.assertEqual(access.phase(), "inspect")
        self.assertTrue(access.focused())
        episode.focus_record = None
        episode.searching = True
        self.assertTrue(access.focused())
        episode.searching = False
        self.assertFalse(access.focused())
        episode.active = True
        self.assertTrue(access.defer_routine())
        episode.active = False
        stub.user_action_pending = True
        self.assertTrue(access.defer_routine())
        with self.assertRaises(RuntimeError):
            access.bind(stub)
