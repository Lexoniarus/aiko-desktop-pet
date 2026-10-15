"""Headless World lifecycle, identity, geometry and ownership regressions."""

from __future__ import annotations

import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from typing import Callable

from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldObjectSnapshot,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldFailure, WorldOperationError, WorldState

FOOD = ObjectDefinition(
    "onigiri", "onigiri", "onigiri", frozenset((ObjectInteraction.EAT,)),
)
FOOTPRINT = ObjectFootprint(8, 12)


class WorldStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = WorldState(WorldSurface(800, 600), (FOOD,))

    def assert_rejected(
        self, reason: WorldFailure, operation: Callable[[], object],
    ) -> None:
        before = self.world.snapshot()
        with self.assertRaises(WorldOperationError) as raised:
            operation()
        self.assertEqual(raised.exception.reason, reason)
        self.assertEqual(self.world.snapshot(), before)

    def place(self, x: float = 100) -> WorldObjectSnapshot:
        return self.world.place_resting("onigiri", x, FOOTPRINT)

    def hold(self) -> WorldObjectSnapshot:
        return self.world.create_held("onigiri", WorldPosition(100, 200), FOOTPRINT)

    def test_identical_portions_have_independent_identity_and_consumption(self) -> None:
        first, second = self.place(), self.place()
        self.assertNotEqual(first.instance_id, second.instance_id)
        held = self.world.collect_resting(
            first.instance_id, expected_revision=first.revision,
        )
        consumed = self.world.consume(held.instance_id, expected_revision=held.revision)
        self.assertEqual(consumed.state, ObjectState.CONSUMED)
        self.assertIsNone(consumed.position)
        self.assertEqual(self.world.get(second.instance_id), second)
        self.assert_rejected(WorldFailure.INVALID_TRANSITION, lambda: (
            self.world.collect_resting(consumed.instance_id,
                                       expected_revision=consumed.revision)
        ))
        self.assert_rejected(WorldFailure.INVALID_TRANSITION, lambda: (
            self.world.consume(consumed.instance_id,
                               expected_revision=consumed.revision)
        ))

    def test_scripted_release_and_ground_contact_preserve_one_portion(self) -> None:
        held = self.hold()
        moved = self.world.move_held(
            held.instance_id, WorldPosition(300, 250), expected_revision=held.revision,
        )
        self.assertEqual(moved.state, ObjectState.USER_HELD)
        falling = self.world.release(
            moved.instance_id, expected_revision=moved.revision,
        )
        self.assertEqual(falling.state, ObjectState.FALLING)
        self.assertEqual(falling.position, WorldPosition(300, 250))
        self.assert_rejected(WorldFailure.INVALID_TRANSITION, lambda: (
            self.world.collect_resting(falling.instance_id,
                                       expected_revision=falling.revision)
        ))
        landed = self.world.land(
            falling.instance_id, expected_revision=falling.revision,
        )
        self.assertEqual(landed.position, WorldPosition(300, 0))
        self.assertEqual(landed.state, ObjectState.RESTING)
        self.assertEqual(len(self.world.snapshot().objects), 1)
        self.assertEqual((held.revision, moved.revision, falling.revision,
                          landed.revision), (0, 1, 2, 3))

    def test_handover_is_an_explicit_release_operation_not_pointer_motion(self) -> None:
        held = self.hold()
        self.assert_rejected(WorldFailure.INVALID_TRANSITION, lambda: (
            self.world.consume(held.instance_id, expected_revision=held.revision)
        ))
        accepted = self.world.accept_handover_on_release(
            held.instance_id, expected_revision=held.revision,
        )
        self.assertEqual(accepted.state, ObjectState.PET_HELD)
        self.assertIsNone(accepted.position)
        self.assertEqual(self.hold().state, ObjectState.USER_HELD)

    def test_one_cursor_and_one_pet_custody_slot(self) -> None:
        held = self.hold()
        self.assert_rejected(WorldFailure.CURSOR_OCCUPIED, self.hold)
        pet_held = self.world.accept_handover_on_release(
            held.instance_id, expected_revision=held.revision,
        )
        second = self.place()
        self.assert_rejected(WorldFailure.PET_OCCUPIED, lambda: (
            self.world.collect_resting(second.instance_id,
                                       expected_revision=second.revision)
        ))
        self.world.consume(pet_held.instance_id, expected_revision=pet_held.revision)
        self.assertEqual(self.world.collect_resting(
            second.instance_id, expected_revision=second.revision,
        ).state, ObjectState.PET_HELD)

    def test_busy_pet_does_not_implicitly_release_a_cursor_item(self) -> None:
        first = self.place()
        self.world.collect_resting(first.instance_id, expected_revision=first.revision)
        held = self.hold()
        self.assert_rejected(WorldFailure.PET_OCCUPIED, lambda: (
            self.world.accept_handover_on_release(held.instance_id,
                                                 expected_revision=held.revision)
        ))
        # The future application handles a refused offer by explicitly releasing.
        self.assertEqual(self.world.release(
            held.instance_id, expected_revision=held.revision,
        ).state, ObjectState.FALLING)

    def test_stale_pointer_release_cannot_undo_newer_movement(self) -> None:
        held = self.hold()
        self.world.move_held(held.instance_id, WorldPosition(200, 200),
                             expected_revision=held.revision)
        self.assert_rejected(WorldFailure.STALE_REVISION, lambda: (
            self.world.release(held.instance_id, expected_revision=held.revision)
        ))

    def test_snapshots_do_not_change_when_objects_move_or_new_items_appear(
        self,
    ) -> None:
        first = self.place()
        before = self.world.snapshot()
        source = self.world.get(first.instance_id)
        moved = self.world.move_resting(first.instance_id, 250,
                                        expected_revision=first.revision)
        self.place(400)
        self.assertEqual(before.objects, (first,))
        self.assertEqual(source.position, WorldPosition(100, 0))
        self.assertEqual(moved.position, WorldPosition(250, 0))
        self.assertEqual(before.revision, 1)
        self.assertEqual(self.world.snapshot().revision, 3)
        with self.assertRaises(FrozenInstanceError):
            setattr(source, "position", WorldPosition(500, 0))
        with self.assertRaises(FrozenInstanceError):
            setattr(before.surface, "width", 10)

    def test_noop_movement_does_not_invalidate_prepared_revision(self) -> None:
        held = self.hold()
        before = self.world.snapshot()
        result = self.world.move_held(held.instance_id, WorldPosition(100, 200),
                                      expected_revision=held.revision)
        self.assertEqual(result, held)
        self.assertEqual(self.world.snapshot(), before)

    def test_footprint_and_height_bounds_are_validated_before_creation(self) -> None:
        for position in (WorldPosition(7, 0), WorldPosition(789, 0),
                         WorldPosition(100, 601)):
            with self.subTest(position=position):
                self.assert_rejected(WorldFailure.OUT_OF_BOUNDS, lambda: (
                    self.world.create_held("onigiri", position, FOOTPRINT)
                ))
        for x in (8, 788):
            self.assertEqual(self.place(x).position, WorldPosition(x, 0))
        self.assert_rejected(WorldFailure.OUT_OF_BOUNDS, lambda: (
            self.world.place_resting("onigiri", 100, ObjectFootprint(400, 401))
        ))

    def test_rejected_relocation_preserves_position_and_revision(self) -> None:
        item = self.place()
        self.assert_rejected(WorldFailure.OUT_OF_BOUNDS, lambda: (
            self.world.move_resting(item.instance_id, 799,
                                    expected_revision=item.revision)
        ))

    def test_terminal_instances_cannot_be_reused_and_ids_do_not_recycle(self) -> None:
        for initial in (ObjectState.USER_HELD, ObjectState.FALLING,
                        ObjectState.RESTING):
            with self.subTest(initial=initial):
                item = self.place() if initial == ObjectState.RESTING else self.hold()
                if initial == ObjectState.FALLING:
                    item = self.world.release(item.instance_id,
                                              expected_revision=item.revision)
                removed = self.world.remove(item.instance_id,
                                            expected_revision=item.revision)
                self.assertEqual(removed.state, ObjectState.REMOVED)
                self.assertIsNone(removed.position)
                self.assert_rejected(WorldFailure.INVALID_TRANSITION, lambda: (
                    self.world.remove(removed.instance_id,
                                      expected_revision=removed.revision)
                ))
                self.assertNotEqual(self.place().instance_id, removed.instance_id)

    def test_wrong_custody_operations_are_rejected_without_partial_change(self) -> None:
        item = self.place()
        for operation in (
            lambda: self.world.release(item.instance_id,
                                       expected_revision=item.revision),
            lambda: self.world.accept_handover_on_release(
                item.instance_id, expected_revision=item.revision,
            ),
            lambda: self.world.land(item.instance_id, expected_revision=item.revision),
            lambda: self.world.consume(item.instance_id,
                                       expected_revision=item.revision),
        ):
            self.assert_rejected(WorldFailure.INVALID_TRANSITION, operation)

    def test_unknown_instances_definitions_and_bad_revisions_leave_world_unchanged(
        self,
    ) -> None:
        self.assert_rejected(WorldFailure.UNKNOWN_DEFINITION, lambda: (
            self.world.place_resting("missing", 100, FOOTPRINT)
        ))
        self.assert_rejected(WorldFailure.UNKNOWN_INSTANCE, lambda: (
            self.world.remove("missing", expected_revision=0)
        ))
        item = self.place()
        for revision in (-1, 1, True):
            self.assert_rejected(WorldFailure.STALE_REVISION, lambda: (
                self.world.remove(item.instance_id, expected_revision=revision)
            ))

    def test_nonfood_definition_cannot_be_consumed(self) -> None:
        self.world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "toy", "toy",
        ),))
        toy = self.world.place_resting("toy", 100, FOOTPRINT)
        held = self.world.collect_resting(
            toy.instance_id, expected_revision=toy.revision,
        )
        self.assert_rejected(WorldFailure.NOT_EDIBLE, lambda: (
            self.world.consume(held.instance_id, expected_revision=held.revision)
        ))

    def test_only_owner_thread_reads_or_mutates_live_world(self) -> None:
        item = self.place()
        snapshot = self.world.snapshot()
        with ThreadPoolExecutor(max_workers=1) as pool:
            for operation in (
                lambda: self.place(),
                self.world.snapshot,
                lambda: self.world.get(item.instance_id),
            ):
                with self.assertRaises(RuntimeError):
                    pool.submit(operation).result()
            self.assertEqual(pool.submit(lambda: snapshot.objects).result(), (item,))
        self.assertEqual(self.world.snapshot(), snapshot)

    def test_definition_list_is_copied_and_duplicate_ids_are_rejected(self) -> None:
        source = [FOOD]
        world = WorldState(WorldSurface(800, 600), source)
        source.clear()
        self.assertEqual(world.snapshot().definitions, (FOOD,))
        with self.assertRaises(ValueError):
            WorldState(WorldSurface(800, 600), (FOOD, FOOD))


class WorldValueTests(unittest.TestCase):
    def test_invalid_geometry_is_rejected(self) -> None:
        for number in (float("nan"), float("inf"), -1.0, True):
            for make in (
                lambda: WorldPosition(number, 0),
                lambda: WorldPosition(0, number),
                lambda: ObjectFootprint(number, 0),
                lambda: ObjectFootprint(0, number),
                lambda: WorldSurface(number, 100),
                lambda: WorldSurface(100, number),
            ):
                with self.subTest(number=number, factory=make):
                    with self.assertRaises(ValueError):
                        make()
        for width, height in ((0, 100), (100, 0)):
            with self.assertRaises(ValueError):
                WorldSurface(width, height)

    def test_edible_capability_and_food_reference_must_agree(self) -> None:
        for definition_id, asset_id, food_id, interactions in (
            ("", "onigiri", None, frozenset()),
            ("onigiri", "bad asset", None, frozenset()),
            ("onigiri", "onigiri", "", frozenset()),
            ("onigiri", "onigiri", "onigiri", frozenset()),
            ("onigiri", "onigiri", None, frozenset((ObjectInteraction.EAT,))),
        ):
            with self.subTest(definition_id=definition_id, food_id=food_id):
                with self.assertRaises(ValueError):
                    ObjectDefinition(definition_id, asset_id, food_id, interactions)
