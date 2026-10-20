"""Coordinate object behavior through the existing subjective/action owners."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..pet.balance import BALANCE
from ..pet.interaction_events import ArrangementDisrupted
from ..pet.mind.object_attention import LookSide, ObjectAttention
from ..pet.mind.object_decisions import (
    ObjectUseContext,
    ObjectUseDecision,
    decide_object_use,
)
from ..pet.mind.object_intentions import ObjectGoal
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..pet.mind.object_perception import ItemPresentation
from ..pet.state import PetState
from ..world.contracts import ObjectState, WorldSnapshot
from ..world.state import WorldState
from .object_awareness import ObjectAwareness
from .object_feedback import InteractionPhase
from .object_interaction import ObjectInteractionCoordinator
from .object_interaction_state import SearchPosition
from .object_orientation import OrientationProgress, has_learned_places


def choose_object_attention(
    phase: InteractionPhase, *, sleeping: bool, game_open: bool,
    walking: float, following_cursor: bool = False,
    activity_active: bool = False,
    tracking_feedback: bool = False,
    orientation_side: LookSide | None = None,
    cursor: tuple[float, float] | None, target: tuple[float, float] | None,
) -> ObjectAttention:
    """Derive attention from the existing action and movement owners only."""
    if sleeping or game_open:
        return ObjectAttention("unavailable", None)
    if phase in (
        "inspect", "recognize", "decide", "handover", "eat",
        "put_down", "finish",
    ):
        return ObjectAttention("object", target)
    if phase in ("await_return", "await_settle", "recognize_offer", "decide_offer"):
        subject = target or cursor
        return ObjectAttention("object", subject, focused_place=subject is not None)
    if phase not in ("idle", "search"):
        return ObjectAttention("object", target, focused_place=target is not None)
    if activity_active and not (following_cursor and tracking_feedback):
        return ObjectAttention("unavailable", None)
    if orientation_side is not None:
        return ObjectAttention("survey", (orientation_side, 0))
    if following_cursor and cursor is not None:
        subject = target or cursor
        return ObjectAttention("object", subject, focused_place=True)
    if walking:
        return ObjectAttention("moving", (1 if walking > 0 else -1, 0))
    if target is not None:
        return ObjectAttention("survey", target)
    if cursor is not None:
        return ObjectAttention("cursor", cursor)
    return ObjectAttention("survey", None)


@dataclass(frozen=True, slots=True)
class SearchMotion:
    """Walk to a World-relative body-center waypoint with route coverage."""

    center: float
    progress: float


@dataclass(frozen=True, slots=True)
class BehaviorFacts:
    """Host facts sampled on the owner thread, without native object references."""

    game_open: bool = False
    character_action_busy: bool = False
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
        self._orientation = OrientationProgress(side=None)

    def request_orientation(self) -> None:
        self._orientation = OrientationProgress(
            side=-1 if has_learned_places(
                self._awareness.memory.snapshot(),
                (0, self._world.snapshot().surface.width),
            ) else None,
        )

    def refresh_after_placement(self) -> None:
        """Notice changed stock when idle, preserving current looks and goals."""
        if (self._orientation.complete and not self._interaction.active
                and self._awareness.intentions.goal is None):
            self.request_orientation()

    def _followed_knowledge(self) -> ObjectKnowledge | None:
        record = self._awareness.following_record
        return self._awareness.memory.get(record) if record is not None else None

    @property
    def orientation_side(self) -> LookSide | None:
        known = self._followed_knowledge()
        if known is not None and known.recognized:
            return None
        return self._orientation.side

    def observe(
        self, snapshot: WorldSnapshot, *, now: float, x: float, width: float,
        presentation: tuple[str, ItemPresentation] | None, facts: BehaviorFacts,
        attention: ObjectAttention,
    ) -> BehaviorObservation:
        interaction, awareness = self._interaction, self._awareness
        memory_before = awareness.memory.snapshot()
        goal_before = awareness.intentions.goal
        checking_before = awareness.checking_absence
        absences_before = {item.token for item in awareness.absences}
        followed_known = self._followed_knowledge()
        transport = followed_known is not None and followed_known.recognized
        bound = (interaction.active and not interaction.searching
                 or attention.mode == "unavailable" or transport)
        if bound:
            self.request_orientation()
        pending = not self._orientation.complete
        coverage = (self._orientation.coverage
                    if pending and not bound and self.orientation_side is not None
                    else None)
        focus = interaction.focus_record
        if focus is None and attention.mode == "object":
            focus = awareness.following_record
        blocked = (
            attention.mode == "unavailable"
            or (interaction.active and not interaction.approaching
             and not interaction.searching and interaction.phase != "found")
            or (facts.carrying and interaction.focus_record is None)
            or facts.game_open
            or (facts.character_action_busy and not interaction.active)
            or self._state.sleeping or facts.playback_busy
            or (self._state.sleep_episode.care_break
                and self._state.satiety >= BALANCE.number("sleep", "food_target"))
        )
        revisit = (not blocked and not bound
                   and self._pending_investigation() is not None)
        goal = awareness.update(
            snapshot, self._state, now=now, x=x, height=0, width=width,
            attention=attention,
            blocked=blocked or interaction.search_active, held_pose=(x, width * .4),
            committed=focus,
            inspecting=interaction.inspection_record,
            presentation=presentation if not pending or interaction.focus_record
            is not None or transport else None,
            known_coverage=coverage, defer_selection=pending or revisit,
        )
        if pending and not bound:
            self._orientation = self._orientation.advance(
                now=now, attention=attention, known=memory_before,
                ground_bounds=(0, snapshot.surface.width),
                duration=BALANCE.number("object_behavior", "absence_seconds"),
                maximum_gap=BALANCE.number("object_behavior", "tracking_gap_seconds"),
            )
            if self._orientation.complete and not revisit:
                goal = awareness.choose_goal(
                    self._state, x=x, now=now,
                    blocked=blocked or interaction.search_active, committed=focus,
                )
        elif not bound and self._orientation.complete and has_learned_places(
            memory_before, (0, snapshot.surface.width),
        ) and (not checking_before and awareness.checking_absence
               or {item.token for item in awareness.absences} - absences_before
               or not interaction.active and goal is not None
               and (goal_before is None or goal_before.token != goal.token)):
            self.request_orientation()
        if not self._orientation.complete and interaction.focus_record is None:
            direction = self.orientation_side
            orientation_gaze = (GazeTarget(attention.origin[0] + direction * width,
                               attention.origin[1]) if direction is not None else
                    GazeTarget(followed_known.x, followed_known.height)
                    if followed_known is not None else None)
            return BehaviorObservation(None, True, orientation_gaze, False, transport)
        if interaction.searching:
            # SearchTask chooses investigations; free appetite cannot steer its look.
            goal = None
        goal = self._check_approach_goal(
            goal, attention=attention, now=now, width=width,
        )
        absence_gaze = self._notice_absences(facts, attention=attention)
        if absence_gaze is not None:
            return BehaviorObservation(goal, blocked, absence_gaze, True, False)
        if revisit and not interaction.active:
            recheck = self._revisit_investigation(attention=attention, now=now)
            if recheck is not None:
                return recheck
            goal = awareness.choose_goal(self._state, x=x, now=now, blocked=blocked)
        gaze_target = self._observation_gaze(
            goal, focus=focus, attention=attention, x=x,
        )
        return BehaviorObservation(
            goal, blocked, gaze_target,
            False, not (awareness.checking_absence or awareness.absences),
        )

    def _pending_investigation(self) -> ObjectKnowledge | None:
        """Read a selected new find, never a missing-item search candidate."""
        if self._interaction.active or self._interaction.search_active:
            return None
        goal = self._awareness.intentions.goal
        known = (self._awareness.memory.get(goal.token)
                 if goal is not None and goal.purpose == "investigate" else None)
        if (known is not None and not known.recognized and known.resting
                and known.place_status == "remembered"):
            return known
        return None

    def _revisit_investigation(
        self, *, attention: ObjectAttention, now: float,
    ) -> BehaviorObservation | None:
        """Look back after orientation; only fresh sensing can admit approach.

        The intention remains with ObjectIntentions. Remembering this unknown
        place grants neither an executable World binding nor a SearchTask.
        """
        awareness = self._awareness
        known = self._pending_investigation()
        if known is None or any(seen.token == known.token
                                for seen in awareness.observations):
            return None
        distance = math.hypot(known.x - attention.origin[0],
                              known.height - attention.origin[1])
        if (distance <= attention.width * BALANCE.number(
            "object_behavior", "notice_widths",
        ) and (not attention.sees(known.x, known.height)
               or awareness.checking_notice or awareness.checking_absence
               or awareness.absences)):
            return BehaviorObservation(None, True, GazeTarget(known.x, known.height),
                                       False, False)
        # Out of range or unresolved after a covered look: release curiosity
        # without claiming a learned portion is missing or starting a patrol.
        awareness.intentions.cancel(now)
        return None

    def _check_approach_goal(
        self, goal: ObjectGoal | None, *, attention: ObjectAttention,
        now: float, width: float,
    ) -> ObjectGoal | None:
        """Release a lost target without inventing absence or switching subjects."""
        interaction, awareness = self._interaction, self._awareness
        record = interaction.memory_id
        if interaction.approaching and record is not None:
            evidence = awareness.target_evidence(
                record, radius=width * BALANCE.number(
                    "object_behavior", "memory_place_widths",
                ),
            )
            known = awareness.memory.get(record)
            if (evidence == "unseen" and attention.mode == "object"
                    and known is not None and known.resting
                    and attention.sees(known.x, known.height)
                    and not awareness.checking_notice):
                # End a lost target association without discovering its neighbour
                # or claiming that a remembered learned place is already missing.
                if not known.recognized:
                    awareness.memory.forget(record)
                self.unreachable(now=now)
                goal = None
            if evidence == "forgotten" or (
                evidence == "unresolved" and known is not None and not known.recognized
            ):
                awareness.memory.forget(record)
                self.unreachable(now=now)
                goal = None
            elif evidence == "unresolved" and interaction.phase == "approach":
                # Release the action so the local unknown can be inspected.
                # Association loss alone establishes no missing learned portion.
                self.unreachable(now=now)
                goal = None
        return goal

    def _notice_absences(
        self, facts: BehaviorFacts, *, attention: ObjectAttention,
    ) -> GazeTarget | None:
        """Acknowledge only losses accepted by the existing feedback owner."""
        interaction, awareness = self._interaction, self._awareness
        can_react = (not self._state.sleeping and not facts.game_open
                     and attention.mode != "unavailable"
                     and (not facts.character_action_busy or interaction.active)
                     and not facts.user_action_pending
                     and not facts.playback_busy)
        losses = sorted(awareness.absences, key=lambda item: not item.recognized)
        absence_gaze = None
        for absent in losses if can_react else ():
            previous = interaction.phase
            if interaction.notice_absence(absent):
                awareness.acknowledge_absence(absent.token)
                if absent.recognized:
                    self._state.experience_interaction(ArrangementDisrupted())
                if previous != interaction.phase:
                    absence_gaze = GazeTarget(absent.x, absent.height)
        return absence_gaze

    def _observation_gaze(
        self, goal: ObjectGoal | None, *, focus: str | None,
        attention: ObjectAttention, x: float,
    ) -> GazeTarget | None:
        """Choose the subject or retain the current unfinished sensory look."""
        awareness = self._awareness
        observed = {item.token for item in awareness.observations}
        visible = [item for item in awareness.memory.snapshot()
                   if not item.assessed and item.token in observed]
        gaze = awareness.memory.get(focus) if focus is not None else None
        target = gaze or goal or (
            min(visible, key=lambda item: abs(item.x - x)) if visible else None
        )
        gaze_target = (GazeTarget(target.x, target.height)
                       if target is not None else None)
        if ((focus is None and (awareness.checking_absence or awareness.absences))
                or gaze_target is None and awareness.checking_notice):
            # Complete the current look before a new find can turn it away.
            gaze_target = GazeTarget(
                attention.origin[0] + attention.direction[0] * attention.width,
                attention.origin[1] + attention.direction[1] * attention.width,
            ) if attention.direction is not None else None
        return gaze_target

    def advance(
        self, goal: ObjectGoal | None, *, blocked: bool,
        search_position: SearchPosition | None = None,
    ) -> Hold | Approach | SearchMotion:
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
        search = self.advance_search(blocked=blocked, position=search_position)
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
        if (known is not None and not known.recognized
                and self._awareness.instance_for_record(goal.token) is None):
            return Hold()
        if not interaction.active and known is not None and not known.resting:
            # A passive held wish waits for observed ground contact.
            return Hold()
        if not interaction.active:
            interaction.begin_goal(goal)
        if interaction.phase == "notice":
            return Hold()
        return Approach(goal)

    def unreachable(self, *, now: float) -> None:
        """The native adapter could not find a reachable standing position."""
        self._awareness.intentions.cancel(now)
        if self._interaction.search_active:
            self._interaction.abandon_candidate()
        else:
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
        if (self._state.sleeping or facts.game_open
                or self._interaction.active and not returning
                or facts.character_action_busy and not returning
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
        if (self._state.sleeping or facts.game_open
                or facts.character_action_busy and not self._interaction.active):
            return False
        known = self._awareness.known_instance(instance)
        if known is None:
            return False
        if (not self._orientation.complete and not self._interaction.active
                and not (known.recognized
                         and self._awareness.following_record == known.token)):
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
        return object_state == ObjectState.RESTING and reachable

    def advance_search(
        self, *, blocked: bool,
        position: SearchPosition | None = None,
    ) -> SearchMotion | Hold | None:
        """Keep the search subject until verified reunion or actual route end."""
        interaction = self._interaction
        if not interaction.searching:
            return None
        if not interaction.search_ready:
            return Hold()
        observed = {seen.token for seen in self._awareness.observations}
        for known in self._awareness.memory.snapshot():
            if (known.token in observed and known.place_status == "remembered"
                    and interaction.found(known.token)):
                return Hold()
        if blocked:
            return Hold()
        if interaction.acute_food_search:
            if self._state.satiety >= BALANCE.number("sleep", "food_target"):
                return Hold()
            for known in self._awareness.memory.snapshot():
                if (known.token in observed and known.kind == "food" and known.resting
                        and known.place_status == "remembered"
                        and decide_object_use(known, self._state).consume):
                    goal = ObjectGoal(
                        known.token, known.identity, known.kind, known.x, known.height,
                        known.observed_at,
                    )
                    self._awareness.intentions.adopt(goal)
                    interaction.begin_goal(goal)
                    return Hold()
        if self._awareness.checking_absence or self._awareness.checking_notice:
            return Hold()
        candidates = [item for item in self._awareness.memory.snapshot()
                      if not item.recognized and item.resting
                      and item.place_status == "remembered"
                      and interaction.can_investigate(item.token)
                      and any(seen.token == item.token
                              for seen in self._awareness.observations)]
        if candidates:
            candidate = min(candidates, key=lambda item: (
                abs(item.x - position.x) if position is not None else item.x,
                item.token,
            ))
            investigation = ObjectGoal(
                candidate.token, None, None, candidate.x, candidate.height,
                candidate.observed_at, "investigate",
            )
            self._awareness.intentions.adopt(investigation)
            interaction.begin_goal(investigation)
            return Hold()
        center = (interaction.search_destination(position)
                  if position is not None else None)
        interaction.complete_search()
        if not interaction.searching:
            return Hold()
        if center is None:
            return Hold()
        return SearchMotion(center, interaction.search_progress)
