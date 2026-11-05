"""Drive the existing reaction/animation contracts without Tk or browser APIs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from ..pet.animation.character import CharacterCatalog, PlaybackEvent
from ..pet.animation.expression import EXPRESSION_CLIPS, Expression
from ..pet.interaction_events import SocialCompletion
from ..pet.mind.catalog import Reaction
from .playback import ReactionPlayer


@dataclass(frozen=True, slots=True)
class SpeechSnapshot:
    text: str
    emote: str
    id: int
    active: bool
    story: bool


class RoomPlayback:
    """One serial timer queue; unread/unshown dialogue cannot earn completion."""

    def __init__(
        self,
        catalog: CharacterCatalog,
        *,
        social_completed: Callable[[SocialCompletion], None],
        mark_spoken: Callable[[], None],
        text_presented: Callable[[str], None] = lambda _event: None,
        wish_presented: Callable[[int], None] = lambda _wish: None,
    ) -> None:
        self._catalog = catalog
        self._timers: dict[str, tuple[float, Callable[[], None]]] = {}
        self._sequence = 0
        self._now = 0.0
        self._text = self._emote = ""
        self._text_id = 0
        self._unshown = False
        self._require_text_ack = True
        self._pending_event: str | None = None
        self._pending_wish: int | None = None
        self._text_presented, self._wish_presented = text_presented, wish_presented
        self.animation = "idle"
        self.expression: Expression | None = None
        self._expression_id = 0
        self._emote_id = 0
        self.can_express: Callable[[], bool] = lambda: False
        self.action_id = 0
        self.action_timings: tuple[int, ...] | None = None
        self.hold_frame: int | None = None
        self._action_timers: list[str] = []
        self.receive: Callable[[PlaybackEvent], None] = lambda _event: None
        self.player = ReactionPlayer(
            schedule=self.schedule,
            cancel_timer=self.cancel_timer,
            display_emote=self._display_emote,
            display_text=self._display_text,
            start_action=self.start_action,
            mark_spoken=mark_spoken,
            is_closed=lambda: False,
            hide_speech=self._hide,
            social_completed=social_completed,
            on_text=lambda event: setattr(self, "_pending_event", event),
            on_wish_text=lambda wish: setattr(self, "_pending_wish", wish),
            express=self.express,
        )

    def schedule(self, milliseconds: int, callback: Callable[[], None]) -> str:
        self._sequence += 1
        token = str(self._sequence)
        self._timers[token] = self._now + milliseconds / 1000, callback
        return token

    def cancel_timer(self, token: str) -> None:
        self._timers.pop(token, None)

    def advance(self, seconds: float) -> None:
        if self._unshown:
            return
        end = self._now + max(0, seconds)
        for _ in range(512):
            due = [
                (token, value)
                for token, value in self._timers.items()
                if value[0] <= end
            ]
            if not due:
                break
            token, (deadline, callback) = min(due, key=lambda item: item[1][0])
            self._timers.pop(token, None)
            self._now = deadline
            callback()
            if self._unshown:
                return
        self._now = end

    def _display_text(self, text: str, _milliseconds: int) -> None:
        self._emote_id += 1
        self._text, self._emote = text, ""
        self._text_id += 1
        self._unshown = self._require_text_ack

    def _display_emote(self, emote: str, milliseconds: int) -> None:
        self._text_id += 1
        self._unshown = False
        self._emote, self._text = emote, ""
        self._emote_id += 1
        current = self._emote_id

        def clear() -> None:
            if current == self._emote_id:
                self._emote = ""

        self.schedule(milliseconds, clear)

    def express(self, value: Expression | None) -> None:
        self._expression_id += 1
        self.expression = value if self.can_express() else None
        if self.expression is None:
            return
        current = self._expression_id
        clip = self._catalog.clip_for(EXPRESSION_CLIPS[self.expression], 2)

        def clear() -> None:
            if current == self._expression_id:
                self.expression = None

        self.schedule(round(clip.duration_seconds * 1000), clear)

    def _hide(self) -> None:
        self._text = self._emote = ""
        self._unshown = False
        self._pending_event = None
        self._pending_wish = None

    def acknowledge(self, text_id: int) -> None:
        if text_id == self._text_id:
            self._unshown = False
            if self._pending_event is not None:
                self._text_presented(self._pending_event)
                self._pending_event = None
            if self._pending_wish is not None:
                self._wish_presented(self._pending_wish)
                self._pending_wish = None

    def next_text(self) -> None:
        if not self._unshown:
            self.player.advance_story()

    def advance_story(self) -> bool:
        return False if self._unshown else self.player.advance_story()

    def comment(self, text: str, milliseconds: int) -> None:
        """Game commentary has its own expiry and never owns gameplay input."""
        self._pending_event = None
        self._pending_wish = None
        self._display_text(text, milliseconds)
        # Optional game commentary must not freeze movement, dealing, drops or
        # input while Aiko is outside the independently controlled camera.
        self._unshown = False
        current = self._text_id
        self.schedule(
            milliseconds, lambda: self._hide() if self._text_id == current else None
        )

    def emote(self, name: str, milliseconds: int) -> None:
        self._display_emote(name, milliseconds)

    def silence(self) -> None:
        self._hide()

    def snapshot(self) -> SpeechSnapshot:
        return SpeechSnapshot(
            self._text,
            self._emote,
            self._text_id,
            self.player.active,
            self.player.story_active,
        )

    def speak(
        self,
        reaction: Reaction | None,
        *,
        completed: Callable[[bool], None] | None = None,
        subject: str | None = None,
        progress: Callable[[int], bool] | None = None,
        animate: bool = True,
        require_presentation: bool = True,
    ) -> None:
        self._require_text_ack = require_presentation
        self.player.play(
            reaction,
            on_complete=completed,
            subject=subject,
            on_progress=progress,
            animate=animate,
        )

    def stop_animation(self) -> None:
        self.action_id += 1
        for token in self._action_timers:
            self.cancel_timer(token)
        self._action_timers.clear()
        self.animation = "idle"
        self.action_timings = None
        self.hold_frame = None

    @property
    def now(self) -> float:
        return self._now

    @property
    def rest_cycle(self) -> float:
        return self._catalog.clip_for("rest-neutral", 2).duration_seconds

    def game_action(
        self,
        name: str,
        duration: int | tuple[int, ...] | None,
        marker: Callable[[int], None],
        done: Callable[[], None],
    ) -> None:
        """Render the existing game marker contract without object/care effects."""
        self.stop_animation()
        self.express(None)
        self.animation = name
        clip = self._catalog.clip_for(name, 2)
        timings = clip.timings
        if isinstance(duration, tuple):
            if len(duration) != len(timings):
                raise ValueError("Game animation timing does not match the clip")
            timings = duration
        elif isinstance(duration, int):
            total = sum(timings)
            boundaries = [
                round(sum(timings[:i]) * duration / total)
                for i in range(len(timings) + 1)
            ]
            timings = tuple(b - a for a, b in zip(boundaries, boundaries[1:]))
        self.action_timings = timings
        elapsed = 0
        for index, milliseconds in enumerate(timings):
            self._action_timers.append(
                self.schedule(elapsed, partial(marker, clip.sprite_index(index)))
            )
            elapsed += milliseconds
        action = self.action_id

        def complete() -> None:
            if self.action_id == action:
                self.stop_animation()
                done()

        self._action_timers.append(self.schedule(elapsed, complete))

    def start_action(self, name: str, _duration: float) -> None:
        action = self.play_animation(name)
        duration = self._catalog.clip_for(name, 2).duration_seconds
        self._action_timers.append(
            self.schedule(
                round(duration * 1000),
                lambda: self.stop_animation() if self.action_id == action else None,
            )
        )

    def play_animation(self, name: str) -> int:
        self.stop_animation()
        self.animation = "pick_up" if name == "hold_item" else name
        clip = self._catalog.clip_for(self.animation, 2)
        action_id = self.action_id
        elapsed = 0
        indices = list(range(len(clip.timings)))
        if name == "hold_item":
            indices = [len(clip.timings) - 1]
            self.hold_frame = clip.sprite_index(indices[0])
        for index in indices:
            source = clip.sprite_index(index)
            events = clip.frames[source].events
            if name == "put_down":
                events = ("detach_object",) if source == 2 else ()
            event = PlaybackEvent(action_id, self.animation, source, events, False)
            self._action_timers.append(
                self.schedule(
                    elapsed,
                    partial(self.receive, event),
                )
            )
            elapsed += clip.timings[index]
        final = PlaybackEvent(
            action_id, self.animation, clip.sprite_index(indices[-1]), (), True
        )
        self._action_timers.append(
            self.schedule(
                elapsed,
                lambda: self.receive(final),
            )
        )
        return action_id

    def suspend(self) -> None:
        self.player.cancel()
        self.stop_animation()
        self._timers.clear()
        self._hide()
