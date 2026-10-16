"""Execute identified object phases; World, mind and presentation keep ownership."""

from __future__ import annotations

from collections.abc import Callable

from ..pet.animation.character import PlaybackEvent
from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.mind.object_decisions import ObjectUseDecision
from ..pet.mind.object_events import ObjectEvent
from ..pet.mind.object_intentions import ObjectGoal
from ..pet.mind.object_memory import ObjectMemory
from ..pet.mind.object_perception import ConsumableKind
from ..pet.mind.object_withholding import (
    WithholdingEpisode,
    choose_withholding_response,
)
from ..world.contracts import ObjectState
from ..world.state import WorldOperationError, WorldState
from .object_custody import ObjectCustody
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
        consume: Callable[[str, str, str, ConsumptionOrigin], bool],
        resolve_instance: Callable[[str], str | None],
        record_for_instance: Callable[[str], str | None],
        can_acquire: Callable[[str], bool], ground_x: Callable[[str], float],
        completed: Callable[[str, bool], None],
        memory: ObjectMemory,
        decide: Callable[[str, ConsumptionOrigin], ObjectUseDecision],
        feedback: Callable[[ObjectFeedback], None], cancel_feedback: Callable[[], None],
        now: Callable[[], float], inspection_seconds: float, search_seconds: float,
        withholding: Callable[[str, float], None] = lambda _key, _loss: None,
    ) -> None:
        self.world = world
        self._custody = ObjectCustody(world, memory)
        self._play, self._stop, self._select_item = play, stop, select_item
        self._consume, self._can_acquire = consume, can_acquire
        self._resolve_instance = resolve_instance
        self._record_for_instance = record_for_instance
        self._ground_x, self._completed = ground_x, completed
        self._memory, self._decide = memory, decide
        self._feedback, self._cancel_feedback = feedback, cancel_feedback
        self._now, self._inspection_seconds = now, inspection_seconds
        self._search_seconds = search_seconds
        self._search_started = 0.0
        self.search_x = 0.0
        self._next_goal: ObjectGoal | None = None
        self.phase: InteractionPhase = "idle"
        self.instance_id: str | None = None
        self.memory_id: str | None = None
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
        self._pending_feedback: ObjectEvent | None = None
        self._auxiliary_key: FeedbackKey | None = None
        self._auxiliary_serial = 0
        self._next_contact_feedback = 0.0
        self._withholding = WithholdingEpisode()
        self._withholding_serial = 0
        self._on_withholding = withholding

    @property
    def active(self) -> bool:
        return self.phase != "idle"

    @property
    def focus_record(self) -> str | None:
        """One committed subject; actual loss releases attention to local search."""
        return (self.memory_id if self.active
                and self.phase not in ("search", "found", "missing") else None)

    @property
    def approaching(self) -> bool:
        return self.phase in ("notice", "approach")

    @property
    def waiting_for_target(self) -> bool:
        return self.phase in ("await_return", "await_settle")

    def target_taken(self, record: str) -> bool:
        """Pause only an observed successful take before Aiko owns the item."""
        if self.focus_record != record or self.phase not in (
            "notice", "approach", "pick_up", "await_settle", "await_return",
        ):
            return False
        if (self.instance_id is not None
                and self.world.get(self.instance_id).state == ObjectState.PET_HELD):
            return False
        self.instance_id = None
        self._action_id = -1
        self._arrived = False
        self._withholding = self._withholding.taken(self._now())
        self._set_phase("await_return")
        self._stop()
        self._announce("object_taken")
        return True

    def observe_target_state(self, state: ObjectState | None) -> None:
        """Use current sensory custody only; loss resumes bounded local search."""
        if not self.waiting_for_target:
            return
        if state != ObjectState.USER_HELD:
            self._withholding = self._withholding.returned()
        if state is None:
            self._set_phase("approach")
            self._cue_done = True
            self.start_search()
        elif state in (ObjectState.FALLING, ObjectState.BOUNCING):
            if self.phase != "await_settle":
                self._set_phase("await_settle")
                self._cue_done = True
        elif (state == ObjectState.RESTING and self._cue_done
              and self._auxiliary_key is None):
            known = self._memory.get(self.memory_id) if self.memory_id else None
            if known is not None:
                self._identity, self._kind = known.identity, known.kind
                self._retrieving = self._known_supply()
            self._set_phase("approach")
            self._announce("object_returned")
        elif (state == ObjectState.USER_HELD and self._cue_done
              and self._auxiliary_key is None):
            response = choose_withholding_response(self._withholding, self._now())
            if response is not None:
                self._withholding = response.episode
                self.request_feedback(response.event)
                if response.irritated:
                    self._withholding_serial += 1
                    self._on_withholding(
                        f"{self._interaction_id}/withholding_{self._withholding_serial}",
                        response.friendship_loss,
                    )

    @property
    def searching(self) -> bool:
        return self.phase == "search"

    @property
    def search_progress(self) -> float:
        return min(1.0, max(0.0, (self._now() - self._search_started)
                            / self._search_seconds))

    @property
    def feedback_key(self) -> FeedbackKey:
        return FeedbackKey(self._interaction_id, self._phase_id)

    def _start(self, token: str, origin: ConsumptionOrigin) -> None:
        self.memory_id, self._origin = token, origin
        self.instance_id = None
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
        self._next_goal = None
        self._withholding = WithholdingEpisode()

    def _set_phase(self, phase: InteractionPhase) -> None:
        self.phase = phase
        self._phase_id += 1
        self._cue_done = self._animation_done = False
        self._pending_feedback = None
        self._auxiliary_key = None
        # Invalidate the prior receipt before cancellation calls back.
        self._cancel_feedback()

    def _announce(self, event: ObjectEvent) -> None:
        assert self.memory_id is not None
        self._feedback(ObjectFeedback(self.feedback_key, event,
                                      self.memory_id, self._identity))

    def request_feedback(self, event: ObjectEvent) -> None:
        """Keep at most one aside; never replace an unfinished phase bubble."""
        if self.focus_record is not None and self._auxiliary_key is None:
            self._pending_feedback = event

    def acknowledge_contact(self) -> bool:
        """Ordinary contact defers to a committed episode, without care effects."""
        if self.focus_record is None:
            return False
        if self._now() >= self._next_contact_feedback:
            self._next_contact_feedback = self._now() + BALANCE.number(
                "object_behavior", "contact_feedback_seconds",
            )
            self.request_feedback("object_busy")
        return True

    def begin_goal(self, goal: ObjectGoal) -> bool:
        if self.active:
            return False
        self._start(goal.token, ConsumptionOrigin.AUTONOMOUS)
        self.search_x = goal.x
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
        known = self._memory.get(self.memory_id) if self.memory_id else None
        return (known is not None and known.recognized and known.assessed
                and known.identity == self._identity and known.kind == self._kind)

    def start_search(self) -> None:
        """The caller has attentively arrived at an empty remembered place."""
        if self.phase != "approach" or self.memory_id is None:
            return
        known = self._memory.get(self.memory_id)
        if known is not None:
            self.search_x = known.x
        self._memory.mark_missing(self.memory_id)
        self._search_started = self._now()
        self._set_phase("search")
        self._stop()
        self._announce("object_search")
        self.update()

    def found(self, goal: ObjectGoal) -> None:
        if not self.searching:
            return
        self._next_goal = goal
        self._identity = goal.identity
        self._set_phase("found")
        self._feedback(ObjectFeedback(self.feedback_key, "object_found",
                                      goal.token, goal.identity))
        self.update()

    def arrive(self) -> None:
        if self.phase == "approach":
            self._arrived = True
            self.update()

    def _pick_up(self) -> None:
        assert self.memory_id is not None
        self.instance_id = self._resolve_instance(self.memory_id)
        if self.instance_id is None or not self._can_acquire(self.instance_id):
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
        record = self._record_for_instance(instance_id)
        returning = self.waiting_for_target and record == self.memory_id
        if (record is None or self.active and not returning
                or not self._can_acquire(instance_id)):
            return False
        item = self.world.get(instance_id)
        self._custody.accept_handover_on_release(
            instance_id, memory_id=record, expected_revision=item.revision,
            now=self._now(),
        )
        if returning:
            self._origin = ConsumptionOrigin.HANDOVER
        else:
            self._start(record, ConsumptionOrigin.HANDOVER)
        self.instance_id = instance_id
        known = self._memory.get(record)
        self._identity = known.identity if known is not None else None
        self._kind = known.kind if known is not None else None
        self._select_item(item.definition_id)
        self._action_id = self._play("hold_item")
        if self._known_supply():
            self._set_phase("handover")
            self._announce("object_handover")
        else:
            self._inspect("object_handover")
        self.update()
        return True

    def _inspect(self, event: ObjectEvent = "object_inspect") -> None:
        self._set_phase("inspect")
        self._inspect_at = self._now()
        self._announce(event)

    def receive_feedback(self, receipt: FeedbackReceipt) -> None:
        if self._auxiliary_key is not None and receipt.key == self._auxiliary_key:
            self._auxiliary_key = None
            return
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
        assert self.memory_id is not None
        attach = event.action_id, "attach_object"
        detach = event.action_id, "detach_object"
        if (self.phase == "pick_up" and "attach_object" in event.events
                and attach not in self._effects):
            if (self._resolve_instance(self.memory_id) != token
                    or not self._can_acquire(token)):
                self._finish(False)
                self._stop()
                return
            item = self.world.get(token)
            try:
                self._custody.collect_resting(
                    token, memory_id=self.memory_id,
                    expected_revision=item.revision, now=self._now(),
                )
            except WorldOperationError:
                self._finish(False)
                self._stop()
                return
            except Exception:
                self._seen.discard(event)
                raise
            self._select_item(item.definition_id)
            self._effects.add(attach)
        if (self.phase == "put_down" and "detach_object" in event.events
                and detach not in self._effects):
            item = self.world.get(token)
            try:
                self._custody.put_down(
                    token, self._ground_x(token), memory_id=self.memory_id,
                    expected_revision=item.revision,
                    now=self._now(), deferred=self._queued is None
                    and self._decision.reason == "not_needed",
                )
            except Exception:
                self._seen.discard(event)
                raise
            self._effects.add(detach)
            self._select_item(None)
        if event.finished:
            self._animation_done = True
        self.update()

    def update(self) -> None:
        """Advance only confirmed prerequisites; injected active time owns dwell."""
        if self._auxiliary_key is not None:
            return
        if (self._pending_feedback is not None and self._cue_done
                and self.memory_id is not None):
            event, self._pending_feedback = self._pending_feedback, None
            self._auxiliary_serial += 1
            self._auxiliary_key = FeedbackKey(
                self._interaction_id, self._phase_id, self._auxiliary_serial,
            )
            self._feedback(ObjectFeedback(self._auxiliary_key, event,
                                          self.memory_id, self._identity))
            return
        for _ in range(12):
            previous = self.phase
            token = self.memory_id
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
                self._memory.mark_assessed(token)
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
            elif self.phase == "handover" and self._cue_done:
                self._begin_eating()
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
            elif (self.phase == "search" and self.search_progress >= 1
                  and self._cue_done):
                self._set_phase("missing")
                self._announce("object_missing")
            elif self.phase == "found" and self._cue_done:
                goal = self._next_goal
                self._set_phase("idle")
                if goal is not None:
                    self.begin_goal(goal)
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
        assert self.memory_id is not None
        item = self.world.get(self.instance_id)
        if item.state != ObjectState.PET_HELD:
            self._finish(False)
            self._stop()
            return
        decision = self._decide(self.memory_id, self._origin)
        self._decision = decision
        if not decision.consume:
            self._set_phase("decide")
            self._announce("object_unknown" if decision.reason == "unrecognized"
                           else "object_later")
            return
        if not self._consume(
            self._interaction_id, self.instance_id, self.memory_id, self._origin,
        ):
            self._put_down()
            return
        self._set_phase("eat")
        self._action_id = self._play("eat")
        self._announce("object_consuming_drink" if self._kind == "drink"
                       else "object_consuming_food")

    def _finish(self, consumed: bool) -> None:
        token = self.instance_id
        record = self.memory_id
        self.instance_id = None
        self.memory_id = None
        self._withholding = WithholdingEpisode()
        self._set_phase("idle")
        self._select_item(None)
        if record is not None:
            consumed = consumed or any(
                item.instance_id == token and item.state == ObjectState.CONSUMED
                for item in self.world.snapshot().objects
            )
            self._completed(record, consumed)
