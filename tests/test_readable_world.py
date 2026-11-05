"""Readable stock is unique in World, independent of menu and reading admission."""

import unittest

from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldFailure, WorldOperationError, WorldState


class ReadableWorldTests(unittest.TestCase):
    def test_duplicate_is_rejected_in_each_custody_before_daily_admission(self):
        definition = ObjectDefinition(
            "book", "book", interactions=frozenset((ObjectInteraction.READ,))
        )
        for custody in ("user", "falling", "resting", "pet"):
            with self.subTest(custody=custody):
                world = WorldState(WorldSurface(800, 600), (definition,))
                item = world.create_held(
                    "book", WorldPosition(100, 100), ObjectFootprint(32, 32)
                )
                if custody != "user":
                    item = world.release(
                        item.instance_id, expected_revision=item.revision
                    )
                if custody in ("resting", "pet"):
                    item = world.land(item.instance_id, expected_revision=item.revision)
                if custody == "pet":
                    item = world.collect_resting(
                        item.instance_id, expected_revision=item.revision
                    )
                before = world.snapshot()
                self.assertFalse(world.can_place_definition("book"))
                with self.assertRaises(WorldOperationError) as raised:
                    world.place_resting("book", 200, ObjectFootprint(32, 32))
                self.assertEqual(
                    raised.exception.reason, WorldFailure.READABLE_ALREADY_PRESENT
                )
                self.assertEqual(world.snapshot(), before)

    def test_removed_book_allows_new_stock_without_reusing_identity(self):
        definition = ObjectDefinition(
            "book", "book", interactions=frozenset((ObjectInteraction.READ,))
        )
        world = WorldState(WorldSurface(800, 600), (definition,))
        first = world.place_resting("book", 100, ObjectFootprint(32, 32))
        world.remove(first.instance_id, expected_revision=first.revision)
        self.assertTrue(world.can_place_definition("book"))
        second = world.place_resting("book", 100, ObjectFootprint(32, 32))
        self.assertNotEqual(first.instance_id, second.instance_id)
        self.assertEqual(world.get(first.instance_id).state, ObjectState.REMOVED)
