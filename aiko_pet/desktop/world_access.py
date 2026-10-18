"""Typed late-binding read port for World callbacks assembled before World."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..application.object_feedback import InteractionPhase
from ..application.object_status import ObjectStatusSnapshot
from ..pet.mind.object_attention import LookSide

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

    def defer_routine(self) -> bool:
        runtime = self._runtime
        return runtime is not None and (
            runtime.interaction.active or runtime.user_action_pending
        )

    def focused(self) -> bool:
        runtime = self._runtime
        return (runtime is not None
                and (runtime.interaction.focus_record is not None
                     or runtime.interaction.searching))

    def contact_feedback_active(self) -> bool:
        runtime = self._runtime
        return runtime is not None and runtime.interaction.contact_feedback_active

    def phase(self) -> InteractionPhase:
        """Read the live episode; before World assembly there is no action."""
        return self._runtime.interaction.phase if self._runtime is not None else "idle"

    def orientation_side(self) -> LookSide | None:
        return self._runtime.orientation_side() if self._runtime is not None else None

    def following_record(self) -> str | None:
        return (self._runtime.awareness.following_record
                if self._runtime is not None else None)

    def object_status(self) -> ObjectStatusSnapshot:
        """Expose detached diagnostics through the existing late-binding port."""
        return (self._runtime.object_status() if self._runtime is not None
                else ObjectStatusSnapshot())
