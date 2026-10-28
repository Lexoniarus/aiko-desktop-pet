"""Select complete pet animation intent outside the Tk sprite renderer.

This desktop orchestrator owns no second pet or action state. It combines
pure pet animation policy with already observed host state and one movement
driver. Frame playback and individual PNG choice remain within AnimatedPet.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Literal, Protocol

from ..pet.animation.ambient import AmbientDirector
from ..pet.animation.animation import SpriteSelection
from ..pet.animation.body_orientation import (
    REACTIVE_TURN_STEP_SECONDS,
    BodyOrientation,
)
from ..pet.animation.character import CharacterCatalog
from ..pet.animation.idle_behaviour import IdleBehaviourProfile
from ..pet.animation.idle_gesture import QUESTION_REQUEST_CLIP
from ..pet.animation.priority import RenderDecision, choose_animation_priority
from ..pet.movement.contracts import WalkStep
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
    ready_for_handover: Callable[[], bool] = lambda: False
    holding_readable: Callable[[], bool] = lambda: False
    cursor_gaze_point: Callable[[], tuple[float, float] | None] = lambda: None
    cancel_action: Callable[[float], None] = lambda _now: None


class DesktopAnimationRuntime:
    """Own animation priorities and passive event selection."""

    def __init__(
        self,
        *,
        state: AnimationNeeds,
        settings: AnimationSettings,
        assets: CharacterCatalog,
        walk: WalkDriver,
        visual: DesktopVisualObservation,
        ports: AnimationRuntimePorts,
    ) -> None:
        self._state = state
        self._settings = settings
        self._assets = assets
        self._has_locomotion = "body-orient-right" in assets.body_clips
        self._walk = walk
        self._visual = visual
        self._ports = ports
        self.ambient = AmbientDirector(started_at=time.monotonic(), body_poses=bool(
            {"body-look-left", "body-look-right"} <= assets.body_clips.keys(),
        ))
        self._body_orientation = BodyOrientation()
        visual.constrain_with(self._body_orientation.constrain_direction)
        self._pointer: tuple[int, int] = (0, 0)
        self._last_pointer_move = -100.0
        self._idle_gesture_front = False

    def advance_walk(
        self,
        now: float,
        elapsed: float,
        *,
        game_mode: bool,
    ) -> str | None:
        """Advance host movement at the current Tk sprite frame cadence."""
        if (
            elapsed > 0
            and self._has_locomotion
            and (
                self._walk.movement.kind == "step"
                or self._walk.movement.source == "cursor"
            )
            and not self._body_orientation.motion_ready
        ):
            return None
        if elapsed > 0 and self._gaze_first:
            axis = self._visual.desired_cursor_gaze()
            if (axis is None or axis not in (*range(2, 7), *range(10, 15))
                    or not self._body_orientation.supports_gaze(axis)):
                return None
        if self._gaze_first:
            self._walk.align_cursor_pace(self._visual.desired_cursor_gaze())
            if self._body_orientation.motion_ready:
                axis = self._visual.desired_cursor_gaze()
                if axis is not None:
                    self._body_orientation.orient_for_gaze_motion(now, axis)
        source = self._walk.movement.source
        step = self._walk.step(
            now,
            elapsed,
            game_mode=game_mode,
            attention_active=(
                self._visual.orienting
                or (self._visual.cursor_watching
                    and self._walk.movement.remaining_distance == 0)
            ),
        )
        if step is None:
            return None
        # A moving frame consumes the old ambient episode first. Its final
        # displacement can then admit one fresh arrival pose, never cancel it
        # again during selection of that same frame.
        self.ambient.suspend(now)
        if (source == "idle" and elapsed > 0 and step.pixels
                and self._walk.movement.remaining_distance == 0):
            self.ambient.finish_outing(now, step.direction)
        return self._motion_clip(step, now)

    def _motion_clip(self, step: WalkStep, now: float) -> str:
        side = "right" if step.direction > 0 else "left"
        if self._gaze_first and self._has_locomotion:
            axis = self._visual.desired_cursor_gaze()
            side = "right" if self._body_orientation.side > 0 else "left"
            if step.kind == "run" and axis in (4, 12):
                return f"running-{side}"
            if axis is not None:
                return f"body-step-{side}-{axis:02}"
        if step.kind != "step" or not self._has_locomotion:
            return f"running-{side}"
        observation = self._visual.observe(
            now,
            self._pointer,
            self._last_pointer_move,
            False,
        )
        axis = observation.gaze_direction
        compatible = axis is not None and (
            2 <= axis <= 6 if step.direction > 0 else 10 <= axis <= 14
        )
        key = f"{axis:02}" if compatible and self._visual.cursor_watching else "profil"
        return f"body-step-{side}-{key}"

    @property
    def _gaze_first(self) -> bool:
        return (self._visual.cursor_watching
                and self._visual.cursor_intent.feeling is not None)

    def _front_gaze(self, direction: int | None, *, refresh: bool) -> RenderDecision:
        self._body_orientation.reset()
        return RenderDecision(
            SpriteSelection("idle", 0) if direction is None
            else SpriteSelection("look", direction),
            clear_action=True,
            refresh_after_ms=(round(REACTIVE_TURN_STEP_SECONDS * 1000)
                              if refresh else None),
        )

    def walk_active(self) -> bool:
        return self._walk.movement.remaining_distance != 0

    def set_idle_profile(self, profile: IdleBehaviourProfile) -> None:
        """Distribute one immutable read; frame callbacks never derive it again."""
        self.ambient.profile = profile
        self._walk.idle_profile = profile

    def interrupt_walk(self) -> None:
        self._walk.movement.interrupt()

    def idle_gesture_duration(self, clip_id: str) -> float:
        return self._assets.clips[clip_id].duration_seconds

    def prepare_idle_gesture(
        self, requested: bool, now: float,
    ) -> Literal["blocked", "turning", "ready"]:
        """Return through actual turn phases; attention owns the bounded request."""
        self._idle_gesture_front = requested and not any((
            self._state.sleeping, self.walk_active(),
            now < self._ports.action_until(), self._visual.cursor_watching,
            self._visual.orienting, self._visual.object_target is not None,
            self._ports.ready_for_handover(), self._ports.holding_readable(),
        ))
        if not self._idle_gesture_front:
            return "blocked"
        return "ready" if self._body_orientation.phase == 0 else "turning"

    def select_animation(
        self,
        now: float,
        pointer: tuple[int, int],
        last_pointer_move: float,
        game_mode: bool,
        active_action: str | None,
    ) -> RenderDecision:
        """Preserve game/sleep/action/walk/gaze/idle priority without Tk."""
        self._pointer, self._last_pointer_move = pointer, last_pointer_move
        if (active_action == QUESTION_REQUEST_CLIP and any((
            game_mode, self._state.sleeping, self._visual.cursor_watching,
            self._visual.orienting, self._visual.object_target is not None,
            self._ports.ready_for_handover(), self._ports.holding_readable(),
        ))):
            self._ports.cancel_action(now)
            active_action = None
        if (
            not game_mode
            and not self._state.sleeping
            and self._ports.holding_readable()
        ):
            self._body_orientation.reset()
            self.ambient.suspend(now)
            return RenderDecision(
                SpriteSelection(
                    "pick_up",
                    fixed_frame=len(self._assets.clips["pick_up"].frames) - 1,
                )
            )
        priority = choose_animation_priority(
            game_mode=game_mode,
            sleeping=self._state.sleeping,
            active_action=active_action,
            action_loops=(
                self._assets.clips[active_action].loop
                if active_action is not None
                else False
            ),
            timed_action_active=now < self._ports.action_until(),
        )
        if priority.mode != "passive":
            self._body_orientation.reset()
            self.ambient.suspend(now)
            if priority.interrupt_walk:
                self.interrupt_walk()
            selected = (
                self._ports.action_clip_id()
                if priority.mode == "timed"
                else priority.animation
            )
            if selected is None:
                raise AssertionError("An active animation needs a clip")
            return RenderDecision(
                SpriteSelection(selected),
                clear_action=priority.clear_action,
            )

        gaze = self._visual.desired_cursor_gaze() if self._gaze_first else None
        if self._gaze_first and not self._body_orientation.supports_gaze(gaze):
            self.ambient.suspend(now)
            return self._front_gaze(gaze, refresh=True)

        walking = self.advance_walk(now, 0, game_mode=game_mode)
        if walking is not None:
            direction = 1 if self._walk.movement.remaining_distance > 0 else -1
            if self._has_locomotion and (
                self._walk.movement.kind == "step"
                or self._walk.movement.source == "cursor"
            ):
                direction = 1 if self._walk.movement.remaining_distance > 0 else -1
                if self._gaze_first:
                    if gaze is None or gaze not in (*range(2, 7), *range(10, 15)):
                        self.ambient.suspend(now)
                        return self._front_gaze(gaze, refresh=False)
                    pose = self._body_orientation.orient_for_gaze_motion(now, gaze)
                    walking = self._motion_clip(
                        WalkStep(0, direction, self._walk.movement.kind), now,
                    )
                else:
                    pose = self._body_orientation.orient_for_motion(now, direction)
                if not self._body_orientation.motion_ready:
                    return RenderDecision(
                        pose, clear_action=True,
                        refresh_after_ms=self._body_orientation.next_delay_ms(now),
                    )
            else:
                self._body_orientation.reset()
            clip = self._assets.body_clips.get(walking)
            rate = (self._walk.speed_pixels_per_second * clip.duration_seconds
                    / (clip.stride * self._walk.settings.scale)
                    if self._gaze_first and clip is not None and clip.stride else 1.0)
            return RenderDecision(
                SpriteSelection(walking), clear_action=True, playback_rate=rate,
                reverse=self._gaze_first and direction != self._body_orientation.side,
            )

        observation = self._visual.observe(
            now,
            pointer,
            last_pointer_move,
            game_mode,
            cursor_gaze_point=self._ports.cursor_gaze_point(),
        )
        if self._ports.ready_for_handover():
            self._body_orientation.reset()
            self.ambient.suspend(now)
            return RenderDecision(
                SpriteSelection(
                    "pick_up",
                    fixed_frame=len(
                        self._assets.clips["pick_up"].frames,
                    )
                    - 1,
                ),
                clear_action=True,
            )
        if (self._idle_gesture_front
                and self.prepare_idle_gesture(True, now) != "blocked"):
            self.ambient.suspend(now)
            selection = self._body_orientation.select(now, SpriteSelection("idle"))
            return RenderDecision(
                selection, clear_action=True,
                refresh_after_ms=self._body_orientation.next_delay_ms(now),
            )
        ambient = self.ambient.select_passive_animation(
            now,
            gaze_direction=observation.gaze_direction,
            observing_computer=self._settings.observe_computer,
            computer_busy=observation.computer_busy,
            energy=self._state.energy,
            mood=self._state.mood,
            satiety=self._state.satiety,
            forward_gaze=observation.forward_gaze,
        )
        selection = ambient.sprite
        if self._assets.body_clips:
            intent = self._visual.cursor_intent
            if self._gaze_first:
                selection = self._body_orientation.select_gaze_stance(
                    now, selection, intent=intent.body, side=intent.side,
                )
            else:
                selection = self._body_orientation.select(
                    now, selection,
                    intent=ambient.body if ambient.side else intent.body,
                    side=ambient.side or intent.side,
                )
            if (ambient.side and self._body_orientation.phase == 4
                    and self._body_orientation.side == ambient.side):
                self.ambient.note_body_settled(now, ambient.side)
        return RenderDecision(
            selection, clear_action=True,
            refresh_after_ms=self._body_orientation.next_delay_ms(now),
        )
