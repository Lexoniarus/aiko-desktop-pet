"""Coordinate one cursor policy with current, read-only activity facts."""

from __future__ import annotations

from dataclasses import dataclass

from ..pet.cursor_experiences import active_cursor_feeling, cursor_impression
from ..pet.interaction_events import (
    CursorExperience,
    CursorWarning,
    CursorWarningReceipt,
)
from ..pet.mind.cursor_behaviour import (
    CursorBehaviourContext,
    CursorBehaviourPolicy,
    CursorIntent,
)
from ..pet.movement.contracts import MotionCompletion
from ..pet.state import PetState
from .cursor_observation import CursorObservation
from .settings import PetSettings


@dataclass(frozen=True, slots=True)
class CursorActivityContext:
    game_open: bool = False
    menu_engaged: bool = False
    foreground_active: bool = False
    world_protected: bool = False
    direct_contact: bool = False

    @property
    def blocked(self) -> bool:
        return (
            self.game_open
            or self.menu_engaged
            or self.foreground_active
            or self.world_protected
            or self.direct_contact
        )


class CursorBehaviourCoordinator:
    """Share one decision; admission never advances or evaluates it again."""

    def __init__(
        self,
        state: PetState,
        settings: PetSettings,
        observer: CursorObservation,
        policy: CursorBehaviourPolicy,
    ) -> None:
        self._state, self._settings = state, settings
        self._observer, self._policy = observer, policy
        self.intent = CursorIntent()
        self._disabled = False
        self._delivered: list[str] = []
        self.feedback: CursorExperience | CursorWarning | None = None

    def reset(self) -> None:
        self.feedback = None
        self._policy.reset()
        self.intent = CursorIntent()

    def claim_access(self, now: float) -> None:
        self.feedback = None
        self._policy.claim_access(now)
        self.intent = self._policy.current

    @property
    def watching(self) -> bool:
        return (
            self._settings.follow_cursor
            and not self._state.sleeping
            and self.intent.gaze
        )

    def begin_frame(self, now: float, context: CursorActivityContext) -> None:
        self.feedback = None
        if (
            not self._settings.follow_cursor
            or self._state.sleeping
            or context.game_open
        ):
            if not self._disabled:
                self._observer.reset()
            self._disabled = True
            self.reset()
            return
        self._disabled = False
        if context.direct_contact:
            self.claim_access(now)
            return
        if context.foreground_active or context.world_protected:
            self._policy.suspend(now)
            self.intent = self._policy.current
            return
        if context.menu_engaged:
            self._policy.pause_for_menu(
                self._observer.current, now,
                feeling=active_cursor_feeling(self._state.moodlets),
            )
            self.intent = self._policy.current
            return
        state = self._state
        feeling = active_cursor_feeling(state.moodlets)
        impression = cursor_impression(state.moodlets)
        self.intent = self._policy.evaluate(
            self._observer.current,
            CursorBehaviourContext(
                state.friendship_level,
                state.energy,
                state.mood,
                state.affection,
                state.fun,
                feeling,
                impression.level if impression is not None and feeling else 0,
            ),
            now,
        )

        if self.intent.warning is not None:
            self.feedback = self.intent.warning
        event = self.intent.experience
        if event is not None and event.evidence_id not in self._delivered:
            self._state.experience_cursor(event)
            if (feeling != event.feeling or impression is None
                    or event.level > impression.level):
                self.feedback = event
            self._delivered = [*self._delivered[-5:], event.evidence_id]

    def admit_motion(
        self, context: CursorActivityContext, now: float
    ) -> CursorIntent | None:
        if (
            context.blocked
            or not self._settings.follow_cursor
            or not self._settings.auto_walk
            or self._state.sleeping
            or not self.intent.moving
            or now > self.intent.until
            or not 0 <= now - self._observer.current.sampled_at <= 0.5
        ):
            return None
        return self.intent

    def note_warning(self, receipt: CursorWarningReceipt) -> None:
        self._policy.note_warning(receipt)

    def finish_motion(self, result: MotionCompletion) -> None:
        if result.source == "cursor":
            self.note_motion_finished(result.token, result.at)

    def note_motion_finished(self, token: int, now: float) -> None:
        self._policy.note_motion_finished(token, now)
        self.intent = self._policy.current
