"""Foreground pickup/eat/put-down execution; presentation reports identified events."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from ..pet.animation.character import PlaybackEvent
from ..pet.consumption import ConsumptionOrigin
from ..world.contracts import ObjectState
from ..world.state import WorldOperationError, WorldState

InteractionPhase = Literal["idle", "pick_up", "put_down", "eat"]


class ObjectInteractionCoordinator:
    def __init__(
        self, world: WorldState, *, play: Callable[[str], int],
        stop: Callable[[], None], select_item: Callable[[str | None], None],
        consume: Callable[[str, str, ConsumptionOrigin], bool],
        eligible: Callable[[str], bool], ground_x: Callable[[str], float],
        completed: Callable[[str, bool], None],
    ) -> None:
        self.world = world
        self._play = play
        self._stop = stop
        self._select_item = select_item
        self._consume = consume
        self._eligible = eligible
        self._ground_x = ground_x
        self._completed = completed
        self.phase: InteractionPhase = "idle"
        self.instance_id: str | None = None
        self._origin = ConsumptionOrigin.AUTONOMOUS
        self._action_id = -1
        self._sequence = 0
        self._interaction_id = ""
        self._queued: Callable[[], None] | None = None
        self._seen: set[PlaybackEvent] = set()

    @property
    def active(self) -> bool:
        return self.phase != "idle"

    def _start(self, instance_id: str, origin: ConsumptionOrigin) -> None:
        self.instance_id = instance_id
        self._origin = origin
        self._sequence += 1
        self._interaction_id = f"interaction_{self._sequence}"
        self._seen.clear()

    def begin_pickup(self, instance_id: str) -> bool:
        if self.active or not self._eligible(instance_id):
            return False
        self._start(instance_id, ConsumptionOrigin.AUTONOMOUS)
        self.phase = "pick_up"
        self._action_id = self._play("pick_up")
        return True

    def offer_on_release(self, instance_id: str) -> bool:
        if self.active or not self._eligible(instance_id):
            return False
        item = self.world.get(instance_id)
        self.world.accept_handover_on_release(instance_id,
                                              expected_revision=item.revision)
        self._start(instance_id, ConsumptionOrigin.HANDOVER)
        self._select_item(item.definition_id)
        self._begin_eating()
        return True

    def interrupt(self, action: Callable[[], None]) -> None:
        """Only unconsumed acquired items need animated recovery."""
        if self.instance_id is not None:
            item = self.world.get(self.instance_id)
            if item.state == ObjectState.PET_HELD:
                self._queued = action
                if self.phase != "put_down" and self.phase != "pick_up":
                    self._put_down()
                return
        if self.active:
            self._finish(False)
            self._stop()
        action()

    def receive(self, event: PlaybackEvent) -> None:
        if (not self.active or event.action_id != self._action_id
                or event.clip_id != self.phase or event in self._seen):
            return
        self._seen.add(event)
        instance_id = self.instance_id
        assert instance_id is not None
        if self.phase == "pick_up" and "attach_object" in event.events:
            if not self._eligible(instance_id):
                self._finish(False)
                self._stop()
                return
            item = self.world.get(instance_id)
            try:
                self.world.collect_resting(instance_id, expected_revision=item.revision)
            except WorldOperationError:
                self._finish(False)
                self._stop()
                return
            self._select_item(item.definition_id)
        if self.phase == "put_down" and "detach_object" in event.events:
            item = self.world.get(instance_id)
            self.world.put_down(instance_id, self._ground_x(instance_id),
                                expected_revision=item.revision)
            self._select_item(None)
        if not event.finished:
            return
        if self.phase == "pick_up":
            if self._queued is not None:
                self._put_down()
            else:
                self._begin_eating()
        elif self.phase == "put_down":
            queued, self._queued = self._queued, None
            self._finish(False)
            self._stop()
            if queued is not None:
                queued()
        elif self.phase == "eat":
            self._finish(True)
            self._stop()

    def _put_down(self) -> None:
        self.phase = "put_down"
        self._action_id = self._play("put_down")

    def _begin_eating(self) -> None:
        assert self.instance_id is not None
        item = self.world.get(self.instance_id)
        if item.state != ObjectState.PET_HELD:
            self._finish(False)
            self._stop()
            return
        if not self._consume(self._interaction_id, self.instance_id, self._origin):
            self._put_down()
            return
        self.phase = "eat"
        self._action_id = self._play("eat")

    def _finish(self, consumed: bool) -> None:
        instance_id = self.instance_id
        self.phase = "idle"
        self.instance_id = None
        self._select_item(None)
        if instance_id is not None:
            self._completed(instance_id, consumed)
