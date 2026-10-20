"""Select complete pet animation intent outside the Tk sprite renderer.

This desktop orchestrator owns no second pet or action state. It combines
pure pet animation policy with already observed host state and one movement
driver. Frame playback and individual PNG choice remain within AnimatedPet.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Protocol

from ..pet.animation.ambient import AmbientDirector
from ..pet.animation.animation import SpriteSelection
from ..pet.animation.character import CharacterCatalog
from ..pet.animation.priority import RenderDecision, choose_animation_priority
from .visual_observation import DesktopVisualObservation
from .walk_runtime import WalkDriver


class AnimationNeeds(Protocol):
    @property
    def sleeping(self) -> bool: ...

    @property
    def energy(self) -> float: ...

    @property
    def mood(self) -> float: ...

    @property
    def satiety(self) -> float: ...


class AnimationSettings(Protocol):
    @property
    def observe_computer(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class AnimationRuntimePorts:
    """Current action and pet attention; no concrete UI references."""

    action_until: Callable[[], float]
    action_clip_id: Callable[[], str]
    attention_until: Callable[[], float]
    ready_for_handover: Callable[[], bool] = lambda: False


class DesktopAnimationRuntime:
    """Own animation priorities and passive event selection."""

    def __init__(
        self, *, state: AnimationNeeds, settings: AnimationSettings,
        assets: CharacterCatalog, walk: WalkDriver,
        visual: DesktopVisualObservation, ports: AnimationRuntimePorts,
    ) -> None:
        self._state = state
        self._settings = settings
        self._assets = assets
        self._walk = walk
        self._visual = visual
        self._ports = ports
        self.ambient = AmbientDirector(started_at=time.monotonic())

    def advance_walk(
        self, now: float, elapsed: float, *, game_mode: bool,
    ) -> str | None:
        """Advance host movement at the current Tk sprite frame cadence."""
        return self._walk.step(
            now, elapsed, game_mode=game_mode,
            attention_active=(now < self._ports.attention_until()
                              or self._visual.orienting),
        )

    def walk_active(self) -> bool:
        return self._walk.movement.remaining_distance != 0

    def interrupt_walk(self) -> None:
        self._walk.movement.interrupt()

    def select_animation(
        self, now: float, pointer: tuple[int, int],
        last_pointer_move: float, game_mode: bool,
        active_action: str | None,
    ) -> RenderDecision:
        """Preserve game/sleep/action/walk/gaze/idle priority without Tk."""
        priority = choose_animation_priority(
            game_mode=game_mode,
            sleeping=self._state.sleeping,
            active_action=active_action,
            action_loops=(
                self._assets.clips[active_action].loop
                if active_action is not None else False
            ),
            timed_action_active=now < self._ports.action_until(),
        )
        if priority.mode != "passive":
            self.ambient.suspend(now)
            if priority.interrupt_walk:
                self.interrupt_walk()
            selected = (
                self._ports.action_clip_id()
                if priority.mode == "timed" else priority.animation
            )
            if selected is None:
                raise AssertionError("An active animation needs a clip")
            return RenderDecision(
                SpriteSelection(selected), clear_action=priority.clear_action,
            )

        walking = self.advance_walk(now, 0, game_mode=game_mode)
        if walking is not None:
            self.ambient.suspend(now)
            return RenderDecision(SpriteSelection(walking), clear_action=True)

        observation = self._visual.observe(
            now, pointer, last_pointer_move, game_mode,
        )
        if self._ports.ready_for_handover():
            self.ambient.suspend(now)
            return RenderDecision(
                SpriteSelection("pick_up", fixed_frame=len(
                    self._assets.clips["pick_up"].frames,
                ) - 1), clear_action=True,
            )
        selection = self.ambient.select_passive_animation(
            now, gaze_direction=observation.gaze_direction,
            observing_computer=self._settings.observe_computer,
            computer_busy=observation.computer_busy,
            energy=self._state.energy, mood=self._state.mood,
            satiety=self._state.satiety,
            forward_gaze=observation.forward_gaze,
        )
        return RenderDecision(selection, clear_action=True)
