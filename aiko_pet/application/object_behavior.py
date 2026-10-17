"""Coordinate object behavior through the existing subjective/action owners."""

from __future__ import annotations

from dataclasses import dataclass

from ..pet.mind.object_decisions import (
    ObjectUseContext,
    ObjectUseDecision,
    decide_object_use,
)
from ..pet.mind.object_intentions import ObjectGoal
from ..pet.mind.object_perception import ItemPresentation
from ..pet.state import PetState
from ..world.contracts import ObjectState, WorldSnapshot
from ..world.state import WorldState
from .object_awareness import ObjectAwareness
from .object_interaction import ObjectInteractionCoordinator


@dataclass(frozen=True, slots=True)
class SearchMotion:
    """Continue searching around this World-relative center and active progress."""

    center: float
    progress: float


@dataclass(frozen=True, slots=True)
class SearchStopped:
    """The episode completed; end this update without another desktop action."""


@dataclass(frozen=True, slots=True)
class BehaviorFacts:
    """Host facts sampled on the owner thread, without native object references."""

    game_open: bool = False
    controls_active: bool = False
    carrying: bool = False
    playback_busy: bool = False
    user_action_pending: bool = False


@dataclass(frozen=True, slots=True)
class GazeTarget:
    x: float
    height: float


@dataclass(frozen=True, slots=True)
class BehaviorObservation:
    """This update's attention decision, applied before offer observation."""

    goal: ObjectGoal | None
    blocked: bool
    gaze: GazeTarget | None
    absence_noticed: bool
    observe_offer: bool


@dataclass(frozen=True, slots=True)
class Hold:
    """Clear the native movement goal for this update."""


@dataclass(frozen=True, slots=True)
class Approach:
    """Translate a subjective target into a real, reachable standing position."""

    target: ObjectGoal


class ObjectBehaviorCoordinator:
    """Coordinate shared owners without storing a second wish or episode.

    Native geometry and movement remain desktop responsibilities. Attention and
    motion are separate steps because offer observation can synchronously change
    the episode between them. Results are local to one update, never stored here.
    """

    def __init__(
        self, state: PetState, awareness: ObjectAwareness,
        interaction: ObjectInteractionCoordinator, world: WorldState,
    ) -> None:
        self._state = state
        self._awareness = awareness
        self._interaction = interaction
        self._world = world

    def observe(
        self, snapshot: WorldSnapshot, *, now: float, x: float, width: float,
        presentation: tuple[str, ItemPresentation] | None, facts: BehaviorFacts,
    ) -> BehaviorObservation:
        interaction, awareness = self._interaction, self._awareness
        blocked = (
            (interaction.active and not interaction.approaching
             and not interaction.searching and interaction.phase != "found")
            or (facts.carrying and interaction.focus_record is None)
            or facts.game_open
            or (facts.controls_active and interaction.focus_record is None)
            or self._state.sleeping or facts.playback_busy
        )
        goal = awareness.update(
            snapshot, self._state, now=now, x=x, height=0, width=width,
            attentive=not self._state.sleeping and not facts.game_open,
            blocked=blocked, held_pose=(x, width * .4),
            committed=interaction.focus_record,
            inspecting=interaction.inspection_record, presentation=presentation,
        )
        can_react = (not self._state.sleeping and not facts.game_open
                     and not facts.controls_active and not facts.user_action_pending
                     and not facts.playback_busy)
        for absent in awareness.absences if can_react else ():
            if interaction.notice_absence(absent):
                awareness.acknowledge_absence(absent.token)
                return BehaviorObservation(
                    goal, blocked, GazeTarget(absent.x, absent.height), True, False,
                )
        observed = {item.token for item in awareness.observations}
        visible = [item for item in awareness.memory.snapshot()
                   if not item.assessed and item.token in observed]
        focus = interaction.focus_record
        gaze = awareness.memory.get(focus) if focus is not None else None
        target = gaze or goal or (
            min(visible, key=lambda item: abs(item.x - x)) if visible else None
        )
        return BehaviorObservation(
            goal, blocked,
            GazeTarget(target.x, target.height) if target is not None else None,
            False, not (awareness.checking_absence or awareness.absences),
        )

    def advance(
        self, goal: ObjectGoal | None, *, blocked: bool,
    ) -> Hold | Approach | SearchMotion | SearchStopped:
        """Continue after native offer observation, preserving same-tick effects."""
        interaction = self._interaction
        if interaction.waiting_for_target:
            record = interaction.memory_id
            instance = (self._awareness.instance_for_record(record)
                        if record is not None else None)
            interaction.observe_target_state(
                self._world.get(instance).state if instance is not None else None,
            )
            # Even a synchronous return acknowledgement holds for this tick.
            return Hold()
        search = self.advance_search(goal, blocked=blocked)
        if search is not None:
            return search
        if interaction.phase == "found":
            return Hold()
        if blocked or goal is None or self._awareness.checking_absence:
            # An active focused approach always has a focus_record. Only end
            # it if the selected wish is truly gone, not while checking an
            # empty remembered place or waiting for its absence reaction.
            if (goal is None and interaction.approaching
                    and not self._awareness.checking_absence
                    and not self._awareness.absences):
                interaction.interrupt(lambda: None)
            return Hold()
        known = self._awareness.memory.get(goal.token)
        if not interaction.active and known is not None and not known.resting:
            # A passive held wish waits for observed ground contact.
            return Hold()
        if interaction.approaching and interaction.memory_id != goal.token:
            interaction.interrupt(lambda: None)
        if not interaction.active:
            interaction.begin_goal(goal)
        if interaction.phase == "notice":
            return Hold()
        return Approach(goal)

    def arrival_unavailable(self, goal: ObjectGoal, *, width: float) -> None:
        """A reached remembered place has no currently collectable binding.

        Physical reach failure is not proof of missing stock. Continue through
        the existing bounded search without claiming an observed empty place.
        """
        if (self._interaction.phase == "approach"
                and self._interaction.memory_id == goal.token
                and not self._awareness.checking_absence
                and not self._awareness.absences
                and not self._awareness.local_notice_pending(
                    x=goal.x, height=goal.height, width=width,
                )):
            self._interaction.start_search(confirmed_empty=False)

    def unreachable(self, *, now: float) -> None:
        """The native adapter could not find a reachable standing position."""
        self._awareness.intentions.cancel(now)
        self._interaction.interrupt(lambda: None)

    def decide(self, token: str, context: ObjectUseContext) -> ObjectUseDecision:
        goal = self._awareness.intentions.goal
        if (goal is not None and goal.token == token
                and goal.use_context == ObjectUseContext.CONTINUING_WISH):
            context = goal.use_context
        return decide_object_use(
            self._awareness.memory.get(token), self._state, context,
        )

    def assess_offer(
        self, instance: str, *, facts: BehaviorFacts,
    ) -> ObjectUseDecision | None:
        record = self._awareness.record_for_instance(instance)
        returning = (self._interaction.waiting_for_target
                     and record == self._interaction.memory_id)
        if (facts.game_open or self._interaction.active and not returning
                or facts.playback_busy):
            return None
        decision = (self._awareness.assess_offer(record, self._state)
                    if record is not None else None)
        if returning and record is not None and decision is not None:
            self._interaction.observe_held_offer(record, decision)
        return decision

    def can_acquire(
        self, instance: str, *, object_state: ObjectState, reachable: bool,
        offer_ready: bool, now: float, facts: BehaviorFacts,
    ) -> bool:
        """Combine current sensory/episode eligibility with native reach evidence."""
        if self._state.sleeping or facts.game_open:
            return False
        known = self._awareness.known_instance(instance)
        if known is None:
            return False
        if object_state == ObjectState.USER_HELD:
            return (
                (not self._interaction.active or self._interaction.waiting_for_target
                 and self._interaction.memory_id == known.token)
                # An unidentified portion may enter Aiko's hands for her
                # first examination; a previously identified one still
                # requires its actual positive current offer assessment.
                and (not known.recognized or (
                    offer_ready and decide_object_use(
                        known, self._state, ObjectUseContext.OFFER,
                    ).consume
                ))
                and not facts.playback_busy and now - known.observed_at < .5
                and any(seen.token == known.token
                        for seen in self._awareness.observations)
                and reachable
            )
        if facts.controls_active and self._interaction.focus_record is None:
            return False
        return object_state == ObjectState.RESTING and reachable

    def advance_search(
        self, goal: ObjectGoal | None, *, blocked: bool,
    ) -> SearchMotion | SearchStopped | None:
        """Return a search instruction, or let the remaining update continue.

        A suitable replacement precedes general blocking, as in the existing
        flow. Cancellation effects use the interaction's normal completion port;
        no separate goal, memory, clock or presentation state is introduced.
        """
        interaction = self._interaction
        if not interaction.searching:
            return None
        known = self._awareness.memory.get(goal.token) if goal is not None else None
        if (goal is not None and goal.token != interaction.memory_id
                and known is not None
                and (goal.purpose == "investigate" and not known.recognized
                     or decide_object_use(known, self._state).consume)):
            interaction.found(goal)
        elif blocked:
            interaction.interrupt(lambda: None)
        else:
            progress = interaction.search_progress
            return SearchMotion(interaction.search_x, progress)
        # Found feedback may complete synchronously. Continue the same desktop
        # update so its existing found/approach/blocking gates see the new state.
        return None
