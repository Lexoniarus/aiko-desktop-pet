"""Typed late-binding World port for observation and elapsed-time application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..application.active_time import SessionInputs
from ..application.object_feedback import InteractionPhase
from ..application.object_status import ObjectStatusSnapshot
from ..pet.mind.object_attention import LookSide
from ..pet.state import PetState

if TYPE_CHECKING:
    from .world_runtime import DesktopWorldRuntime


class WorldRuntimeAccess:
    """Reference the one World owner; keep no second gameplay state or timer."""

    def __init__(self) -> None:
        self._runtime: DesktopWorldRuntime | None = None

    def bind(self, runtime: DesktopWorldRuntime) -> None:
        if self._runtime is not None:
            raise RuntimeError("World runtime is already bound")
        self._runtime = runtime

    def advance(self, state: PetState, inputs: SessionInputs, elapsed: float) -> None:
        """Delegate elapsed-time application to the one restored World session."""
        if self._runtime is None:
            raise RuntimeError("World must be bound before advancing the session")
        self._runtime.time_progression.advance(state, inputs, elapsed)

    def defer_routine(self) -> bool:
        runtime = self._runtime
        return runtime is not None and runtime.defer_sleep()

    def arrangement_ready(self) -> bool:
        """Only resolved live search/place evidence permits conversational relief."""
        runtime = self._runtime
        return runtime is not None and runtime.arrangement_ready()

    def focused(self) -> bool:
        runtime = self._runtime
        return (runtime is not None
                and (runtime.interaction.focus_record is not None
                     or runtime.interaction.searching))

    def contact_feedback_active(self) -> bool:
        runtime = self._runtime
        return runtime is not None and runtime.interaction.contact_feedback_active

    def cursor_protected(self) -> bool:
        """Expose current commitment without introducing another focus owner."""
        runtime = self._runtime
        return runtime is not None and (
            runtime.interaction.active or runtime.user_action_pending
            or runtime.cursor.carrying or runtime.interaction.searching
            or runtime.orientation_side() is not None
        )

    def phase(self) -> InteractionPhase:
        """Read the live episode; before World assembly there is no action."""
        return self._runtime.interaction.phase if self._runtime is not None else "idle"

    def orientation_side(self) -> LookSide | None:
        return self._runtime.orientation_side() if self._runtime is not None else None

    def following_record(self) -> str | None:
        return (self._runtime.awareness.following_record
                if self._runtime is not None else None)

    def holding_readable(self) -> bool:
        return self._runtime is not None and self._runtime.holding_readable()

    def ready_for_handover(self) -> bool:
        """Read live offer eligibility without initiating an interaction."""
        return self._runtime is not None and self._runtime.ready_for_handover()

    def cursor_gaze_point(self) -> tuple[float, float] | None:
        """Read the visible center of the currently followed cursor item."""
        return (self._runtime.cursor_gaze_point()
                if self._runtime is not None else None)

    def object_status(self) -> ObjectStatusSnapshot:
        """Expose detached diagnostics through the existing late-binding port."""
        return (self._runtime.object_status() if self._runtime is not None
                else ObjectStatusSnapshot())
