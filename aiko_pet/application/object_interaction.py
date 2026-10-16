"""Execute identified object phases; World, mind and presentation keep ownership."""

from __future__ import annotations

from collections.abc import Callable

from ..pet.animation.character import PlaybackEvent
from ..pet.consumption import ConsumptionOrigin
from ..pet.mind.object_decisions import ObjectUseDecision
from ..pet.mind.object_events import ObjectEvent
from ..pet.mind.object_intentions import ObjectGoal
from ..pet.mind.object_memory import ObjectMemory
from ..pet.mind.object_perception import ConsumableKind
from ..world.contracts import ObjectState
from ..world.state import WorldOperationError, WorldState
from .object_feedback import (
    FeedbackKey,
    FeedbackReceipt,
    InteractionPhase,
    ObjectFeedback,
)


class ObjectInteractionCoordinator:
    def __init__(
        self, world: WorldState, *, play: Callable[[str], int],
        stop: Callable[[], None], select_item: Callable[[str | None], None],
        consume: Callable[[str, str, ConsumptionOrigin], bool],
        eligible: Callable[[str], bool], ground_x: Callable[[str], float],
        completed: Callable[[str, bool], None],
        memory: ObjectMemory,
        decide: Callable[[str, ConsumptionOrigin], ObjectUseDecision],
        feedback: Callable[[ObjectFeedback], None], cancel_feedback: Callable[[], None],
        now: Callable[[], float], inspection_seconds: float,
    ) -> None:
        self.world = world
        self._play, self._stop, self._select_item = play, stop, select_item
        self._consume, self._eligible = consume, eligible
        self._ground_x, self._completed = ground_x, completed
        self._memory, self._decide = memory, decide
        self._feedback, self._cancel_feedback = feedback, cancel_feedback
        self._now, self._inspection_seconds = now, inspection_seconds
        self.phase: InteractionPhase = "idle"
        self.instance_id: str | None = None
        self._origin = ConsumptionOrigin.AUTONOMOUS
        self._action_id = -1
        self._sequence = self._phase_id = 0
        self._interaction_id = ""
        self._identity: str | None = None
        self._queued: Callable[[], None] | None = None
        self._seen: set[PlaybackEvent] = set()
        self._effects: set[tuple[int, str]] = set()
        self._cue_done = self._animation_done = self._arrived = False
        self._inspect_at = 0.0
        self._decision = ObjectUseDecision(False, "unrecognized")
        self._retrieving = False
        self._kind: ConsumableKind | None = None

    @property
    def active(self) -> bool:
        return self.phase != "idle"

    @property
    def approaching(self) -> bool:
        return self.phase in ("notice", "approach")

    @property
    def feedback_key(self) -> FeedbackKey:
        return FeedbackKey(self._interaction_id, self._phase_id)

    def _start(self, token: str, origin: ConsumptionOrigin) -> None:
        self.instance_id, self._origin = token, origin
        self._sequence += 1
        self._interaction_id = f"interaction_{self._sequence}"
        self._queued = None
        self._seen.clear()
        self._effects.clear()
        self._identity = None
        self._arrived = False
        self._decision = ObjectUseDecision(False, "unrecognized")
        self._retrieving = False
        self._kind = None

    def _set_phase(self, phase: InteractionPhase) -> None:
        self.phase = phase
        self._phase_id += 1
        self._cue_done = self._animation_done = False
        # Invalidate the prior receipt before cancellation calls back.
        self._cancel_feedback()

    def _announce(self, event: ObjectEvent) -> None:
        assert self.instance_id is not None
        self._feedback(ObjectFeedback(self.feedback_key, event,
                                      self.instance_id, self._identity))

    def begin_goal(self, goal: ObjectGoal) -> bool:
        if self.active:
            return False
        self._start(goal.token, ConsumptionOrigin.AUTONOMOUS)
        self._identity = goal.identity
        known = self._memory.get(goal.token)
        self._kind = known.kind if known is not None else None
        self._retrieving = (
            goal.purpose == "consume" and self._known_supply()
        )
        self._set_phase("notice")
        if self._retrieving:
            saved = known is not None and known.disposition == "deferred"
            self._announce(
                ("object_recall_saved_drink" if saved else "object_recall_drink")
                if self._kind == "drink" else
                ("object_recall_saved_food" if saved else "object_recall_food"),
            )
        else:
            self._announce("object_notice")
        self.update()
        return True

    def _known_supply(self) -> bool:
        known = self._memory.get(self.instance_id) if self.instance_id else None
        return (known is not None and known.recognized and known.examined
                and known.identity == self._identity and known.kind == self._kind)

    def missing(self) -> None:
        """Only the caller's completed attentive local search may establish absence."""
        if self.phase != "approach" or self.instance_id is None:
            return
        self._memory.forget(self.instance_id)
        self._set_phase("missing")
        self._announce("object_missing")
        self.update()

    def arrive(self) -> None:
        if self.phase == "approach":
            self._arrived = True
            self.update()

    def _pick_up(self) -> None:
        assert self.instance_id is not None
        if not self._eligible(self.instance_id):
            self._finish(False)
            self._stop()
            return
        self._set_phase("pick_up")
        self._action_id = self._play("pick_up")
        if self._retrieving:
            self._cue_done = True
        else:
            self._announce("object_pick_up")

    def offer_on_release(self, instance_id: str) -> bool:
        if self.active or not self._eligible(instance_id):
            return False
        item = self.world.get(instance_id)
        world_checkpoint, memory_checkpoint = (
            self.world.snapshot(), self._memory.snapshot(),
        )
        try:
            self.world.accept_handover_on_release(instance_id,
                                                  expected_revision=item.revision)
            self._memory.note_acquired(instance_id, now=self._now())
        except Exception:
            self.world.restore_snapshot(world_checkpoint)
            self._memory.restore_snapshot(memory_checkpoint)
            raise
        self._start(instance_id, ConsumptionOrigin.HANDOVER)
        known = self._memory.get(instance_id)
        self._identity = known.identity if known is not None else None
        self._kind = known.kind if known is not None else None
        self._select_item(item.definition_id)
        self._action_id = self._play("hold_item")
        self._inspect("object_handover")
        self.update()
        return True

    def _inspect(self, event: ObjectEvent = "object_inspect") -> None:
        self._set_phase("inspect")
        self._inspect_at = self._now()
        self._announce(event)

    def receive_feedback(self, receipt: FeedbackReceipt) -> None:
        if not self.active or receipt.key != self.feedback_key or self._cue_done:
            return
        self._cue_done = True
        if not receipt.completed and self.phase not in ("put_down", "finish"):
            self.interrupt(lambda: None)

    def interrupt(self, action: Callable[[], None]) -> None:
        if self.phase == "put_down":
            self._queued = action
            self._cue_done = True
            self._cancel_feedback()
            return
        if self.instance_id is not None:
            item = next((item for item in self.world.snapshot().objects
                         if item.instance_id == self.instance_id), None)
            if item is not None and item.state == ObjectState.PET_HELD:
                self._queued = action
                self._cue_done = True
                self._cancel_feedback()
                if self.phase != "pick_up":
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
        token = self.instance_id
        assert token is not None
        attach = event.action_id, "attach_object"
        detach = event.action_id, "detach_object"
        if (self.phase == "pick_up" and "attach_object" in event.events
                and attach not in self._effects):
            if not self._eligible(token):
                self._finish(False)
                self._stop()
                return
            item = self.world.get(token)
            world_checkpoint, memory_checkpoint = (
                self.world.snapshot(), self._memory.snapshot(),
            )
            try:
                self.world.collect_resting(token, expected_revision=item.revision)
                self._memory.note_acquired(token, now=self._now())
            except WorldOperationError:
                self.world.restore_snapshot(world_checkpoint)
                self._memory.restore_snapshot(memory_checkpoint)
                self._finish(False)
                self._stop()
                return
            except Exception:
                self.world.restore_snapshot(world_checkpoint)
                self._memory.restore_snapshot(memory_checkpoint)
                self._seen.discard(event)
                raise
            self._select_item(item.definition_id)
            self._effects.add(attach)
        if (self.phase == "put_down" and "detach_object" in event.events
                and detach not in self._effects):
            item = self.world.get(token)
            world_checkpoint, memory_checkpoint = (
                self.world.snapshot(), self._memory.snapshot(),
            )
            try:
                placed = self.world.put_down(token, self._ground_x(token),
                                             expected_revision=item.revision)
                assert placed.position is not None
                self._memory.note_placement(
                    token, x=placed.position.x, height=placed.position.height,
                    now=self._now(), deferred=self._queued is None
                    and self._decision.reason == "not_needed",
                )
            except Exception:
                self.world.restore_snapshot(world_checkpoint)
                self._memory.restore_snapshot(memory_checkpoint)
                self._seen.discard(event)
                raise
            self._effects.add(detach)
            self._select_item(None)
        if event.finished:
            self._animation_done = True
        self.update()

    def update(self) -> None:
        """Advance only confirmed prerequisites; injected active time owns dwell."""
        for _ in range(12):
            previous = self.phase
            token = self.instance_id
            if token is None:
                return
            if self.phase == "notice" and self._cue_done:
                self._set_phase("approach")
                if self._retrieving:
                    self._cue_done = True
                else:
                    self._announce("object_approach")
            elif self.phase == "approach" and self._arrived and self._cue_done:
                self._pick_up()
            elif self.phase == "pick_up" and self._animation_done and self._cue_done:
                if self._queued is not None:
                    self._put_down()
                elif self._retrieving and self._known_supply():
                    self._begin_eating()
                else:
                    self._retrieving = False
                    self._inspect()
            elif (self.phase == "inspect" and self._cue_done
                  and self._now() - self._inspect_at >= self._inspection_seconds):
                known = self._memory.get(token)
                self._identity = known.identity if known is not None else None
                self._kind = known.kind if known is not None else None
                self._memory.mark_examined(token)
                self._set_phase("recognize")
                self._announce(
                    "object_recognized" if self._identity else "object_unknown",
                )
            elif self.phase == "recognize" and self._cue_done:
                self._decision = self._decide(token, self._origin)
                self._set_phase("decide")
                self._announce(
                    "object_want" if self._decision.consume else
                    "object_unknown" if self._decision.reason == "unrecognized"
                    else "object_later",
                )
            elif self.phase == "decide" and self._cue_done:
                if self._decision.consume:
                    self._begin_eating()
                else:
                    self._put_down()
            elif (self.phase in ("eat", "put_down") and self._animation_done
                  and self._cue_done):
                if self.phase == "put_down":
                    queued, self._queued = self._queued, None
                    self._finish(False)
                    self._stop()
                    if queued is not None:
                        queued()
                else:
                    self._set_phase("finish")
                    self._announce(
                        "object_finished_drink" if self._kind == "drink"
                        else "object_finished_food",
                    )
            elif self.phase == "finish" and self._cue_done:
                self._finish(True)
                self._stop()
            elif self.phase == "missing" and self._cue_done:
                self._finish(False)
                self._stop()
            if self.phase == previous:
                return

    def _put_down(self) -> None:
        self._set_phase("put_down")
        self._action_id = self._play("put_down")
        if self._queued is None:
            self._announce("object_put_down")
        else:
            self._cue_done = True

    def _begin_eating(self) -> None:
        assert self.instance_id is not None
        item = self.world.get(self.instance_id)
        if item.state != ObjectState.PET_HELD:
            self._finish(False)
            self._stop()
            return
        decision = self._decide(self.instance_id, self._origin)
        self._decision = decision
        if not decision.consume:
            self._set_phase("decide")
            self._announce("object_unknown" if decision.reason == "unrecognized"
                           else "object_later")
            return
        if not self._consume(
            self._interaction_id, self.instance_id, self._origin,
        ):
            self._put_down()
            return
        self._set_phase("eat")
        self._action_id = self._play("eat")
        self._announce("object_consuming_drink" if self._kind == "drink"
                       else "object_consuming_food")

    def _finish(self, consumed: bool) -> None:
        token = self.instance_id
        self.instance_id = None
        self._set_phase("idle")
        self._select_item(None)
        if token is not None:
            consumed = consumed or any(
                item.instance_id == token and item.state == ObjectState.CONSUMED
                for item in self.world.snapshot().objects
            )
            self._completed(token, consumed)
