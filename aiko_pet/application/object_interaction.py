"""Execute identified object phases; World, mind and presentation keep ownership."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import replace

from ..pet.animation.character import PlaybackEvent
from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.interaction_events import (
    InteractionEvent,
    WithholdingEnded,
    WithholdingObserved,
)
from ..pet.mind.object_decisions import ObjectUseContext, ObjectUseDecision
from ..pet.mind.object_events import ObjectEvent
from ..pet.mind.object_intentions import ObjectGoal
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..pet.mind.object_memory import ObjectMemory
from ..pet.mind.object_withholding import choose_withholding_response
from ..world.contracts import ObjectState
from ..world.state import WorldOperationError, WorldState
from .object_custody import ObjectCustody
from .object_feedback import (
    FeedbackKey,
    FeedbackReceipt,
    InteractionPhase,
    ObjectFeedback,
)
from .object_interaction_state import (
    AnimationPhase,
    ApproachPhase,
    CuePhase,
    DecisionPhase,
    IdlePhase,
    InspectionPhase,
    InteractionEpisode,
    PhaseFeedback,
    PhaseState,
    PutDownPhase,
    SearchPhase,
    SearchPosition,
    SearchTask,
    WaitingPhase,
)


class ObjectInteractionCoordinator:
    def __init__(
        self, world: WorldState, *, play: Callable[[str], int],
        stop: Callable[[], None], select_item: Callable[[str | None], None],
        consume: Callable[[str, str, str, ConsumptionOrigin], bool],
        resolve_instance: Callable[[str], str | None],
        record_for_instance: Callable[[str], str | None],
        can_acquire: Callable[[str], bool], ground_x: Callable[[str], float],
        hand_type_conflicts: Callable[[str, str], bool],
        completed: Callable[[str, bool], None],
        memory: ObjectMemory,
        decide: Callable[[str, ObjectUseContext], ObjectUseDecision],
        feedback: Callable[[ObjectFeedback], None], cancel_feedback: Callable[[], None],
        now: Callable[[], float], inspection_seconds: float,
        experience: Callable[[InteractionEvent], object] = lambda _event: None,
        withholding_active: Callable[[], bool] = lambda: False,
        withholding: Callable[[str, float], None] = lambda _key, _loss: None,
    ) -> None:
        self.world = world
        self._custody = ObjectCustody(world, memory)
        self._play, self._stop, self._select_item = play, stop, select_item
        self._consume, self._can_acquire = consume, can_acquire
        self._hand_type_conflicts = hand_type_conflicts
        self._resolve_instance = resolve_instance
        self._record_for_instance = record_for_instance
        self._ground_x, self._completed = ground_x, completed
        self._memory, self._decide = memory, decide
        self._feedback, self._cancel_feedback = feedback, cancel_feedback
        self._now, self._inspection_seconds = now, inspection_seconds
        self._search: SearchTask | None = None
        self._missing_feedback: deque[ObjectKnowledge] = deque()
        self._phase: PhaseState = IdlePhase()
        self._active_episode: InteractionEpisode | None = None
        self._sequence = self._phase_id = 0
        self._auxiliary_serial = 0
        self._next_contact_feedback = 0.0
        self._withholding_serial = 0
        self._on_withholding = withholding
        self._experience = experience
        self._withholding_active = withholding_active

    @property
    def _episode(self) -> InteractionEpisode:
        """Require the canonical record inside an episode-owned operation."""
        assert self._active_episode is not None
        return self._active_episode

    @property
    def memory_id(self) -> str | None:
        return (self._active_episode.memory_id
                if self._active_episode is not None else None)

    @property
    def instance_id(self) -> str | None:
        return (self._active_episode.instance_id
                if self._active_episode is not None else None)

    @property
    def phase(self) -> InteractionPhase:
        return self._phase.name

    @property
    def _phase_feedback(self) -> PhaseFeedback:
        assert not isinstance(self._phase, IdlePhase)
        return self._phase.feedback

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
    def inspection_record(self) -> str | None:
        """First identification is eligible only during actual hand inspection."""
        return self.memory_id if self.phase == "inspect" else None

    @property
    def waiting_for_target(self) -> bool:
        return self.phase in (
            "await_return", "await_settle", "recognize_offer", "decide_offer",
        )

    def observe_held_offer(self, record: str, decision: ObjectUseDecision) -> None:
        """Reappraise the observed target without borrowing pet-held phases."""
        state = self._phase
        known = self._memory.get(record)
        if (not isinstance(state, WaitingPhase) or record != self.memory_id
                or known is None or not known.recognized
                or decision.reason in ("unrecognized", "unavailable")):
            return
        if self._search is not None:
            self._announce_identification(known)
            self.update()
            return
        state.appraisal.latest = decision
        self.update()

    def target_taken(self, record: str) -> bool:
        """Pause only an observed successful take before Aiko owns the item."""
        if self.focus_record != record or self.phase not in (
            "notice", "approach", "pick_up", "await_settle", "await_return",
            "recognize_offer", "decide_offer",
        ):
            return False
        if (self.instance_id is not None
                and self.world.get(self.instance_id).state == ObjectState.PET_HELD):
            return False
        self._episode.instance_id = None
        wants = self._decide(record, self._episode.use_context).consume
        self._episode.withholding = self._episode.withholding.taken(self._now())
        if wants:
            existing_impression = self._withholding_active()
            self._experience(WithholdingObserved(repeated_take=True))
            # A repeated take already reinforces an existing impression; the
            # first subsequent complaint must not count the same take again.
            if existing_impression:
                self._episode.withholding = replace(
                    self._episode.withholding, moodlet_trigger_at=self._now(),
                )
        self._set_phase(WaitingPhase("await_return"))
        self._stop()
        self._announce("object_taken")
        return True

    def observe_target_state(self, state: ObjectState | None) -> None:
        """Use sensory custody; loss retires unknowns or searches learned stock."""
        phase = self._phase
        if not isinstance(phase, WaitingPhase):
            return
        episode = self._episode
        if (state != ObjectState.USER_HELD
                and episode.withholding.held_since is not None):
            episode.withholding = episode.withholding.returned()
            self._experience(WithholdingEnded())
        if phase.name in ("recognize_offer", "decide_offer"):
            # Motion cannot replace an unfinished recognition/decision cue.
            return
        if state is None:
            known = self._memory.get(episode.memory_id)
            self._finish(False)
            if known is not None:
                if known.recognized:
                    self._memory.mark_missing(known.token)
                    self.notice_absence(known)
                else:
                    self._memory.forget(known.token)
        elif state in (ObjectState.FALLING, ObjectState.BOUNCING):
            if phase.name != "await_settle":
                waiting = WaitingPhase("await_settle", phase.appraisal)
                self._set_phase(waiting)
                waiting.feedback.completed = True
        elif (state == ObjectState.RESTING and phase.feedback.completed
              and not phase.feedback.blocking_aside):
            known = self._memory.get(self.memory_id) if self.memory_id else None
            if known is not None:
                episode.identity, episode.kind = known.identity, known.kind
                episode.retrieving = self._known_supply()
            self._set_phase(ApproachPhase())
            self._announce("object_returned")
        elif (state == ObjectState.USER_HELD and phase.feedback.completed
              and not phase.feedback.blocking_aside):
            if not self._decide(episode.memory_id, episode.use_context).consume:
                episode.withholding = episode.withholding.returned()
                self._experience(WithholdingEnded())
                return
            response = choose_withholding_response(episode.withholding, self._now())
            if response is not None:
                episode.withholding = response.episode
                self.request_feedback(response.event)
                if response.irritated:
                    self._experience(WithholdingObserved(response.reinforces_moodlet))
                    self._withholding_serial += 1
                    self._on_withholding(
                        f"{episode.interaction_id}/withholding_{self._withholding_serial}",
                        response.friendship_loss,
                    )

    @property
    def searching(self) -> bool:
        return self.phase == "search"

    @property
    def search_active(self) -> bool:
        return self._search is not None

    @property
    def contact_feedback_active(self) -> bool:
        """An optional click reply describes the action without owning it."""
        return self.active and self._phase_feedback.contact_active

    @property
    def search_ready(self) -> bool:
        return (self.searching and self._phase_feedback.completed
                and not self._phase_feedback.blocking_aside
                and not self._missing_feedback)

    def can_investigate(self, token: str) -> bool:
        return self._search is not None and self._search.can_investigate(token)

    def abandon_candidate(self) -> None:
        """An unreachable find ends this action, not the enclosing search."""
        if self._search is not None and self.memory_id is not None:
            self._search.exclude_candidate(self.memory_id)
        self._finish(False)
        self._stop()

    @property
    def search_progress(self) -> float:
        return self._search.progress if self._search is not None else 0.0

    def search_destination(self, position: SearchPosition) -> float | None:
        """Accept actual position as route evidence on the owner thread."""
        task = self._search
        if not self.searching or task is None:
            return None
        return task.destination(position)

    def complete_search(self) -> None:
        """The behavior owner has exhausted route, local evidence and finds."""
        if (self._search is None or not self.search_ready
                or not self._search.route_complete):
            return
        if self._search.acute_food:
            self._search = None
            self._finish(False)
            self._stop()
            return
        self._search = None
        self._set_phase(CuePhase("missing"))
        self._stop()
        self._announce("object_missing")

    def _resume_search(self) -> None:
        task = self._search
        subject = task.next_subject if task is not None else None
        if task is not None and task.acute_food:
            self._start("", ConsumptionOrigin.AUTONOMOUS)
            self._set_phase(SearchPhase())
            self._phase_feedback.completed = True
            return
        if subject is None:
            self._search = None
            self._missing_feedback.clear()
            return
        self._start(subject.token, ConsumptionOrigin.AUTONOMOUS)
        self._episode.identity, self._episode.kind = subject.identity, subject.kind
        self._set_phase(SearchPhase())
        self._phase_feedback.completed = True

    @property
    def feedback_key(self) -> FeedbackKey:
        # Idle diagnostics retain the last ID without retaining the ended episode.
        interaction_id = (self._active_episode.interaction_id
                          if self._active_episode is not None else
                          f"interaction_{self._sequence}" if self._sequence else "")
        return FeedbackKey(interaction_id, self._phase_id)

    def _start(self, token: str, origin: ConsumptionOrigin) -> None:
        self._sequence += 1
        self._active_episode = InteractionEpisode(
            f"interaction_{self._sequence}", token, origin,
            ObjectUseContext.OFFER if origin == ConsumptionOrigin.HANDOVER
            else ObjectUseContext.SUPPLY,
        )

    def _set_phase(self, phase: PhaseState) -> None:
        self._phase = phase
        self._phase_id += 1
        # Invalidate the prior receipt before cancellation calls back.
        self._cancel_feedback()

    def _announce(self, event: ObjectEvent) -> None:
        episode = self._episode
        self._feedback(ObjectFeedback(self.feedback_key, event,
                                      episode.memory_id, episode.identity))

    def request_feedback(self, event: ObjectEvent) -> None:
        """Keep at most one aside; never replace an unfinished phase bubble."""
        if self.active:
            feedback = self._phase_feedback
            if feedback.aside is None:
                feedback.pending = event

    def _announce_aside(
        self, event: ObjectEvent, record: str, identity: str | None,
    ) -> None:
        self._auxiliary_serial += 1
        key = FeedbackKey(
            self._episode.interaction_id, self._phase_id, self._auxiliary_serial,
        )
        cue = ObjectFeedback(key, event, record, identity)
        self._phase_feedback.aside = cue
        self._feedback(cue)

    def acknowledge_contact(self) -> bool:
        """Ordinary contact defers to a committed episode, without care effects."""
        if not self.active:
            return False
        if self._now() >= self._next_contact_feedback:
            self._next_contact_feedback = self._now() + BALANCE.number(
                "object_behavior", "contact_feedback_seconds",
            )
            self.request_feedback("object_busy_search" if self.search_active
                                  else "object_busy")
        return True

    def begin_goal(self, goal: ObjectGoal) -> bool:
        if self.active and not self.searching:
            return False
        self._start(goal.token, ConsumptionOrigin.AUTONOMOUS)
        episode = self._episode
        episode.use_context = goal.use_context
        episode.identity = goal.identity
        known = self._memory.get(goal.token)
        episode.kind = known.kind if known is not None else None
        episode.retrieving = (
            goal.purpose == "consume" and self._known_supply()
        )
        if self._search is not None and not self._known_identity():
            # This approach examines a recovery candidate within the same task.
            self._set_phase(ApproachPhase())
            self._announce("object_approach")
            self.update()
            return True
        self._set_phase(CuePhase("notice"))
        if episode.retrieving and goal.use_context == ObjectUseContext.CONTINUING_WISH:
            self._announce("object_collect_wanted")
        elif episode.retrieving:
            saved = known is not None and known.disposition == "deferred"
            self._announce(
                ("object_recall_saved_drink" if saved else "object_recall_drink")
                if episode.kind == "drink" else
                ("object_recall_saved_food" if saved else "object_recall_food"),
            )
        else:
            self._announce("object_consider_known" if self._known_identity()
                           else "object_notice")
        self.update()
        return True

    def _known_supply(self) -> bool:
        known = self._memory.get(self.memory_id) if self.memory_id else None
        return known is not None and known.assessed and self._known_identity()

    def _known_identity(self) -> bool:
        known = self._memory.get(self.memory_id) if self.memory_id else None
        return (known is not None and known.recognized
                and known.identity == self._episode.identity
                and known.kind == self._episode.kind)

    def _consider_use(self) -> None:
        assert self.memory_id is not None
        decision = self._decide(self.memory_id, self._episode.use_context)
        if decision.reason not in ("unrecognized", "unavailable"):
            self._memory.mark_assessed(self.memory_id)
        self._set_phase(DecisionPhase(decision))
        self._announce(
            "object_want" if decision.consume else
            "object_unknown" if decision.reason == "unrecognized"
            else "object_later",
        )

    def notice_absence(self, known: ObjectKnowledge) -> bool:
        """Give a checked empty place priority, using the existing action owner."""
        if self._search is not None:
            if not known.recognized:
                self._memory.forget(known.token)
                return True
            if not self._search.add(known):
                return False
            self._missing_feedback.append(known)
            return True
        if self.active and (not self.approaching or self.memory_id != known.token):
            return False
        if not self.active:
            self._start(known.token, ConsumptionOrigin.AUTONOMOUS)
        self._episode.identity, self._episode.kind = known.identity, known.kind
        if known.recognized:
            self._search = SearchTask(known, known=self._memory.snapshot())
        # Confirmed absence comes before other discoveries even if Aiko
        # does not currently need to consume that remembered item.
        self._set_phase(CuePhase("notice_absence"))
        self._stop()
        self._announce("object_place_missing")
        return True

    @property
    def acute_food_search(self) -> bool:
        return self._search is not None and self._search.acute_food

    def start_food_search(self) -> None:
        """Use the same route/investigation owner without a fictitious lost item."""
        if self.active:
            return
        self._search = SearchTask(None, known=self._memory.snapshot())
        self._start("", ConsumptionOrigin.AUTONOMOUS)
        self._set_phase(SearchPhase())
        self._phase_feedback.completed = True

    def start_search(self) -> None:
        """Start one task for confirmed missing learned portions."""
        if (self.phase not in ("approach", "notice_absence")
                or self.memory_id is None):
            return
        known = self._memory.get(self.memory_id)
        if known is None or not known.recognized:
            record = self.memory_id
            self._memory.forget(record)
            self._finish(False)
            self._stop()
            return
        self._memory.mark_missing(self.memory_id)
        if self._search is None:
            self._search = SearchTask(known, known=self._memory.snapshot())
        self._set_phase(SearchPhase())
        self._stop()
        self._announce("object_search")
        self.update()

    def found(self, record: str) -> bool:
        """Resolve a verified remembered finding without inventing an action goal."""
        known = self._memory.get(record)
        if known is None or not self._reunite(known):
            return False
        self.update()
        return True

    def _reunite(self, known: ObjectKnowledge) -> bool:
        """Resolve one learned portion and announce its result for every entry."""
        subject = self._search.resolve(known) if self._search is not None else None
        if subject is None:
            return False
        known = self._memory.reunite_search(subject, known.token)
        self._missing_feedback = deque(
            item for item in self._missing_feedback if item.token != subject.token
        )
        if self.searching:
            self._start(known.token, ConsumptionOrigin.AUTONOMOUS)
        self._episode.identity, self._episode.kind = known.identity, known.kind
        self._set_phase(CuePhase("found"))
        self._announce("object_found")
        return True

    def _announce_identification(self, known: ObjectKnowledge) -> None:
        """Choose the result cue once the hand/face evidence identifies a portion."""
        if not self._reunite(known):
            self._episode.identity, self._episode.kind = known.identity, known.kind
            self._set_phase(CuePhase("recognize"))
            self._announce("object_recognized")

    def _complete_recognition(self, token: str) -> None:
        """Recheck losses accepted while the recognition cue was being read."""
        if self._search is None:
            self._consider_use()
            return
        if self._search.acute_food:
            self._consider_use()
            return
        known = self._memory.get(token)
        if known is not None and self._reunite(known):
            return
        decision = self._decide(token, ObjectUseContext.SUPPLY)
        if decision.reason not in ("unrecognized", "unavailable"):
            self._memory.mark_assessed(token)
        if (self.instance_id is not None and self.world.get(
            self.instance_id,
        ).state == ObjectState.PET_HELD):
            self._put_down(defer_if_uninterrupted=decision.reason == "not_needed")
        else:
            self._finish(False)

    def arrive(self) -> None:
        if isinstance(self._phase, ApproachPhase):
            self._phase.arrived = True
            self.update()

    def _pick_up(self) -> None:
        assert self.memory_id is not None
        self._episode.instance_id = self._resolve_instance(self.memory_id)
        if self.instance_id is None or not self._can_acquire(self.instance_id):
            self.abandon_candidate()
            return
        state = AnimationPhase("pick_up")
        self._set_phase(state)
        state.playback.action_id = self._play("pick_up")
        if self._episode.retrieving:
            state.feedback.completed = True
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
        if not returning:
            self._start(record, ConsumptionOrigin.HANDOVER)
        episode = self._episode
        if returning:
            episode.origin = ConsumptionOrigin.HANDOVER
            episode.use_context = ObjectUseContext.OFFER
        episode.instance_id = instance_id
        known = self._memory.get(record)
        episode.identity = known.identity if known is not None else None
        episode.kind = known.kind if known is not None else None
        self._select_item(item.definition_id)
        self._play("hold_item")
        if self._known_identity():
            self._set_phase(CuePhase("handover"))
            self._announce("object_handover")
        else:
            self._inspect()
        self.update()
        return True

    def _inspect(self, event: ObjectEvent = "object_inspect") -> None:
        state = InspectionPhase(started_at=0.0)
        self._set_phase(state)
        state.started_at = self._now()
        self._announce(event)

    def receive_feedback(self, receipt: FeedbackReceipt) -> None:
        state = self._phase
        if isinstance(state, IdlePhase):
            return
        feedback = state.feedback
        if feedback.aside is not None and receipt.key == feedback.aside.key:
            feedback.aside = None
            return
        if receipt.key != self.feedback_key or feedback.completed:
            return
        feedback.completed = True
        if not receipt.completed and state.name not in ("put_down", "finish"):
            self.interrupt(lambda: None)

    def interrupt(self, action: Callable[[], None]) -> None:
        self._search = None
        self._missing_feedback.clear()
        if isinstance(self._phase, PutDownPhase):
            self._episode.queued = action
            self._phase.feedback.completed = True
            self._cancel_feedback()
            return
        if self.instance_id is not None:
            item = next((item for item in self.world.snapshot().objects
                         if item.instance_id == self.instance_id), None)
            if item is not None and item.state == ObjectState.PET_HELD:
                self._episode.queued = action
                self._phase_feedback.completed = True
                self._cancel_feedback()
                if self.phase != "pick_up":
                    self._put_down()
                return
        if self.active:
            self._finish(False)
            self._stop()
        action()

    def receive(self, event: PlaybackEvent) -> None:
        state = self._phase
        if (not isinstance(state, (AnimationPhase, PutDownPhase))
                or event.action_id != state.playback.action_id
                or event.clip_id != state.name or event in self._episode.seen):
            return
        episode = self._episode
        episode.seen.add(event)
        token = self.instance_id
        assert token is not None
        assert self.memory_id is not None
        attach = event.action_id, "attach_object"
        detach = event.action_id, "detach_object"
        if (state.name == "pick_up" and "attach_object" in event.events
                and attach not in episode.effects):
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
                episode.seen.discard(event)
                raise
            self._select_item(item.definition_id)
            episode.effects.add(attach)
        if (isinstance(state, PutDownPhase) and "detach_object" in event.events
                and detach not in episode.effects):
            item = self.world.get(token)
            try:
                self._custody.put_down(
                    token, self._ground_x(token), memory_id=self.memory_id,
                    expected_revision=item.revision, now=self._now(),
                    deferred=episode.queued is None and state.defer_if_uninterrupted,
                )
            except Exception:
                episode.seen.discard(event)
                raise
            episode.effects.add(detach)
            self._select_item(None)
        if event.finished:
            state.playback.finished = True
        self.update()

    def _complete_pickup(self, episode: InteractionEpisode, record: str) -> None:
        """Choose the next hand phase after confirmed pickup playback."""
        if episode.queued is not None:
            self._put_down()
        elif (episode.instance_id is not None
              and self._hand_type_conflicts(record, episode.instance_id)):
            # A local type hypothesis cannot skip safety-critical inspection.
            episode.retrieving = False
            episode.identity, episode.kind = None, None
            self._inspect()
        elif episode.retrieving and self._known_supply():
            self._begin_eating()
        elif self._known_identity():
            self._consider_use()
        else:
            episode.retrieving = False
            self._inspect()

    def _advance_waiting(self, state: WaitingPhase, record: str) -> None:
        """Reappraise a held offer using the same episode and feedback ordering."""
        appraisal = state.appraisal
        if state.name in ("await_return", "await_settle"):
            if appraisal.latest is None:
                return
            known = self._memory.get(record)
            if (known is None or not known.recognized
                    or (self._known_identity()
                        and appraisal.decision == appraisal.latest)):
                return
            already_known = self._known_identity()
            self._episode.identity, self._episode.kind = known.identity, known.kind
            appraisal.decision = appraisal.latest
            self._set_phase(WaitingPhase(
                "decide_offer" if already_known else "recognize_offer", appraisal,
            ))
            self._announce(
                ("object_offer" if appraisal.decision.consume
                 else "object_refuse") if already_known else "object_recognized",
            )
        elif state.name == "recognize_offer":
            if appraisal.latest is not None:
                appraisal.decision = appraisal.latest
            self._set_phase(WaitingPhase("decide_offer", appraisal))
            self._announce("object_offer" if appraisal.decision.consume
                           else "object_refuse")
        elif state.name == "decide_offer":
            if (appraisal.latest is not None
                    and appraisal.latest != appraisal.decision):
                appraisal.decision = appraisal.latest
                self._set_phase(WaitingPhase("decide_offer", appraisal))
                self._announce("object_offer" if appraisal.decision.consume
                               else "object_refuse")
            elif appraisal.decision.consume:
                waiting = WaitingPhase("await_return", appraisal)
                self._set_phase(waiting)
                waiting.feedback.completed = True
            else:
                self._finish(False)
                self._stop()

    def _complete_use_animation(
        self, state: AnimationPhase | PutDownPhase, episode: InteractionEpisode,
    ) -> None:
        """Finish eating or safe put-down separately from phase dispatch."""
        if isinstance(state, PutDownPhase):
            queued, episode.queued = episode.queued, None
            self._finish(False)
            self._stop()
            if queued is not None:
                queued()
        else:
            self._set_phase(CuePhase("finish"))
            self._announce(
                "object_finished_drink" if episode.kind == "drink"
                else "object_finished_food",
            )

    def update(self) -> None:
        """Advance only confirmed prerequisites; injected active time owns dwell."""
        if isinstance(self._phase, IdlePhase):
            return
        feedback = self._phase.feedback
        if feedback.blocking_aside:
            return
        if (feedback.completed and self.phase in ("notice_absence", "search")
                and self._missing_feedback):
            missing = self._missing_feedback.popleft()
            self._announce_aside(
                "object_place_missing", missing.token, missing.identity,
            )
            return
        if (feedback.pending is not None and feedback.completed
                and self.memory_id is not None):
            event, feedback.pending = feedback.pending, None
            self._announce_aside(event, self.memory_id, self._episode.identity)
            return
        for _ in range(12):
            state = self._phase
            token = self.memory_id
            if isinstance(state, IdlePhase) or token is None:
                return
            previous = state.name
            episode = self._episode
            cue_done = state.feedback.completed
            if isinstance(state, CuePhase) and state.name == "notice" and cue_done:
                approach = ApproachPhase()
                self._set_phase(approach)
                if episode.retrieving:
                    approach.feedback.completed = True
                else:
                    self._announce("object_approach")
            elif (isinstance(state, CuePhase) and state.name == "notice_absence"
                  and cue_done):
                if episode.identity is None:
                    self._memory.forget(token)
                    self._finish(False)
                    self._stop()
                else:
                    self.start_search()
            elif isinstance(state, ApproachPhase) and state.arrived and cue_done:
                self._pick_up()
            elif (isinstance(state, AnimationPhase) and state.name == "pick_up"
                  and state.playback.finished and cue_done):
                self._complete_pickup(episode, token)
            elif (isinstance(state, InspectionPhase) and cue_done
                  and self._now() - state.started_at >= self._inspection_seconds):
                known = self._memory.get(token)
                if known is None or not known.recognized:
                    return
                self._announce_identification(known)
            elif (isinstance(state, CuePhase) and state.name == "recognize"
                  and cue_done):
                self._complete_recognition(token)
            elif isinstance(state, WaitingPhase) and cue_done:
                self._advance_waiting(state, token)
            elif isinstance(state, CuePhase) and state.name == "handover" and cue_done:
                self._begin_eating()
            elif isinstance(state, DecisionPhase) and cue_done:
                if state.decision.consume:
                    self._begin_eating()
                else:
                    self._put_down(
                        defer_if_uninterrupted=state.decision.reason == "not_needed",
                    )
            elif (isinstance(state, (AnimationPhase, PutDownPhase))
                  and state.name in ("eat", "put_down")
                  and state.playback.finished and cue_done):
                self._complete_use_animation(state, episode)
            elif isinstance(state, CuePhase) and state.name == "finish" and cue_done:
                self._finish(True)
                self._stop()
            elif isinstance(state, CuePhase) and state.name == "missing" and cue_done:
                self._finish(False)
                self._stop()
            elif isinstance(state, CuePhase) and state.name == "found" and cue_done:
                if (self.instance_id is not None
                        and self.world.get(self.instance_id).state
                        == ObjectState.PET_HELD):
                    known = self._memory.get(token)
                    self._put_down(defer_if_uninterrupted=(
                        known is not None and known.disposition == "deferred"
                    ))
                else:
                    self._finish(False)
            if self.phase == previous:
                return

    def _put_down(self, *, defer_if_uninterrupted: bool = False) -> None:
        state = PutDownPhase(defer_if_uninterrupted)
        self._set_phase(state)
        state.playback.action_id = self._play("put_down")
        if self._episode.queued is None:
            self._announce("object_put_down")
        else:
            state.feedback.completed = True

    def _begin_eating(self) -> None:
        assert self.instance_id is not None
        assert self.memory_id is not None
        episode = self._episode
        item = self.world.get(self.instance_id)
        if item.state != ObjectState.PET_HELD:
            self._finish(False)
            self._stop()
            return
        decision = self._decide(self.memory_id, episode.use_context)
        if not decision.consume:
            self._set_phase(DecisionPhase(decision))
            self._announce("object_unknown" if decision.reason == "unrecognized"
                           else "object_later")
            return
        self._memory.mark_assessed(self.memory_id)
        if not self._consume(
            episode.interaction_id, self.instance_id, self.memory_id, episode.origin,
        ):
            self._put_down(defer_if_uninterrupted=decision.reason == "not_needed")
            return
        state = AnimationPhase("eat")
        self._set_phase(state)
        state.playback.action_id = self._play("eat")
        self._announce("object_consuming_drink" if episode.kind == "drink"
                       else "object_consuming_food")

    def _finish(self, consumed: bool) -> None:
        token = self.instance_id
        record = self.memory_id
        if self._active_episode is not None and (
            self._episode.withholding.held_since is not None
        ):
            self._experience(WithholdingEnded())
        self._active_episode = None
        self._set_phase(IdlePhase())
        self._select_item(None)
        if record is not None:
            consumed = consumed or any(
                item.instance_id == token and item.state == ObjectState.CONSUMED
                for item in self.world.snapshot().objects
            )
            self._completed(record, consumed)
        self._resume_search()
