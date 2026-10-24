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
        self.assertFalse(access.contact_feedback_active())
        self.assertFalse(access.defer_routine())
        self.assertEqual(access.phase(), "idle")
        self.assertIsNone(access.following_record())
        self.assertIsNone(access.orientation_side())
        episode = SimpleNamespace(
            active=False, focus_record=None, searching=False, phase="idle",
            contact_feedback_active=False,
        )
        awareness = SimpleNamespace(following_record=None)
        side = [-1]
        game = [False]
        stub = cast(DesktopWorldRuntime, SimpleNamespace(
            interaction=episode, user_action_pending=False,
            awareness=awareness, orientation_side=lambda: side[0],
            defer_sleep=lambda: episode.active or stub.user_action_pending or game[0],
        ))
        access.bind(stub)
        self.assertEqual(access.orientation_side(), -1)
        side[0] = 1
        self.assertEqual(access.orientation_side(), 1)
        self.assertFalse(access.focused())
        self.assertFalse(access.defer_routine())
        game[0] = True
        self.assertTrue(access.defer_routine())
        game[0] = False
        awareness.following_record = "memory_1"
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
        episode.contact_feedback_active = True
        self.assertTrue(access.contact_feedback_active())
        episode.active = True
        self.assertTrue(access.defer_routine())
        episode.active = False
        stub.user_action_pending = True
        self.assertTrue(access.defer_routine())
        with self.assertRaises(RuntimeError):
            access.bind(stub)
