"""Desktop preference actions and their coordinated component effects.

Preferences alter existing owners; this object does not duplicate state,
create widgets or decide pet dialogue. Persistence is supplied as a port.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from ..application.activity import ActivityCoordinator
from ..application.attention import AttentionCoordinator
from ..application.settings import PetSettings, SettingKey
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.routine import TimeContext, context_at
from ..ui.pet_view.animated_pet import AnimatedPet
from ..ui.pet_view.desktop_window import DesktopWindow
from ..ui.pet_view.speech_presenter import SpeechPresenter
from ..ui.windows.hover_ui import HoverUi
from .visual_observation import DesktopVisualObservation
from .walk_runtime import WalkDriver
from .window_stack import WindowStack


@dataclass(frozen=True, slots=True)
class DesktopPreferencePorts:
    """Side effects beyond the existing preference and window owners."""

    place_x: Callable[[float], None]
    save: Callable[[], None]
    set_context: Callable[[TimeContext], None]
    social_sources_changed: Callable[[bool], None] = lambda _enabled: None
    reset_cursor: Callable[[], None] = lambda: None


class DesktopPreferences:
    """Own the effects of desktop settings, scale and toolbar placement."""

    def __init__(
        self, *, settings: PetSettings,
        adaptive: AdaptiveRoutine, activity: ActivityCoordinator,
        attention: AttentionCoordinator, animated: AnimatedPet,
        walk: WalkDriver, visual: DesktopVisualObservation,
        window: DesktopWindow, hover: HoverUi, speech: SpeechPresenter,
        overlay_stack: WindowStack, ports: DesktopPreferencePorts,
    ) -> None:
        self._settings = settings
        self._adaptive = adaptive
        self._activity = activity
        self._attention = attention
        self._animated = animated
        self._walk = walk
        self._visual = visual
        self._window = window
        self._hover = hover
        self._speech = speech
        self._stack = overlay_stack
        self._ports = ports

    def set_option(self, name: SettingKey, enabled: bool) -> None:
        """Route only supported toggle keys, never mutate settings by name."""
        handlers: dict[SettingKey, Callable[[bool], None]] = {
            "always_on_top": self.set_topmost,
            "auto_walk": self.set_auto_walk,
            "auto_routine": self.set_auto_routine,
            "follow_cursor": self.set_follow_cursor,
            "spontaneous_talk": self.set_spontaneous_talk,
            "observe_computer": self.set_observe_computer,
            "learn_rhythm": self.set_learn_rhythm,
            "online_social": self.set_online_social,
        }
        handler = handlers.get(name)
        if handler is None:
            raise ValueError(f"Unknown setting: {name}")
        handler(enabled)

    def set_topmost(self, value: bool) -> None:
        self._settings.always_on_top = bool(value)
        self._stack.enabled = self._settings.always_on_top
        self._window.set_topmost(self._settings.always_on_top)
        self._hover.set_topmost(self._settings.always_on_top)
        self._speech.set_topmost(self._settings.always_on_top)
        self._stack.restore()
        self._ports.save()

    def set_auto_walk(self, value: bool) -> None:
        self._ports.reset_cursor()
        self._walk.set_auto_walk(value, time.monotonic())
        self._ports.save()

    def set_auto_routine(self, enabled: bool) -> None:
        self._settings.auto_routine = bool(enabled)
        self._activity.advance_state(time.time())
        self._ports.set_context(context_at(time.time()))
        if self._hover.toolbar is not None:
            self._hover.toolbar.refresh()
        self._hover.refresh_status()
        self._ports.save()

    def set_follow_cursor(self, enabled: bool) -> None:
        self._ports.reset_cursor()
        self._settings.follow_cursor = bool(enabled)
        self._visual.reset()
        self._ports.save()

    def set_spontaneous_talk(self, enabled: bool) -> None:
        self._attention.set_spontaneous_talk(enabled, time.monotonic())
        self._ports.save()

    def set_learn_rhythm(self, enabled: bool) -> None:
        self._settings.learn_rhythm = bool(enabled)
        self._ports.save()

    def set_online_social(self, enabled: bool) -> None:
        self._settings.online_social = bool(enabled)
        self._ports.social_sources_changed(self._settings.online_social)
        self._ports.save()

    def set_zodiac(self, sign: str | None) -> None:
        self._settings.zodiac_sign = sign
        self._ports.save()

    def forget_rhythm(self) -> None:
        self._adaptive.forget_profile()
        self._hover.refresh_status()
        self._ports.save()

    def set_observe_computer(self, enabled: bool) -> None:
        self._activity.set_observation_enabled(enabled)
        if self._hover.toolbar is not None:
            self._hover.toolbar.refresh()
        self._ports.save()

    def toggle_scale(self) -> None:
        self._ports.reset_cursor()
        center = (self._settings.x or 0) + self._window.width / 2
        self._settings.scale = 2 if self._settings.scale == 1 else 1
        self._window.resize()
        self._animated.reload_sprites()
        self._visual.reset()
        # Force a Tk geometry update even for an unchanged x/y position.
        self._window.placed = False
        self._ports.place_x(center - self._window.width / 2)
        if self._hover.toolbar is not None and self._hover.toolbar.visible:
            self._hover.toolbar.place()
        self._ports.save()

    def reset_toolbar_position(self) -> None:
        if self._hover.toolbar is not None:
            self._hover.toolbar.reset_position()
        else:
            self._settings.toolbar_x = None
            self._settings.toolbar_y = None
            self._ports.save()

    def center(self) -> None:
        track = self._window.track
        self._ports.place_x(
            (track.left + track.right - self._window.width) / 2,
        )
        self._walk.movement.interrupt()
        self._ports.save()

    def record_toolbar_position(
        self, x: int | None, y: int | None,
    ) -> None:
        self._settings.toolbar_x = x
        self._settings.toolbar_y = y
        if x is not None:
            self._hover.last_hover = time.monotonic()
        self._ports.save()
