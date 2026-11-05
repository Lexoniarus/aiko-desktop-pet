"""Drive the existing reaction/animation contracts without Tk or browser APIs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..pet.animation.character import CharacterCatalog, PlaybackEvent
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
        self, catalog: CharacterCatalog, *,
        social_completed: Callable[[SocialCompletion], None],
        mark_spoken: Callable[[], None],
    ) -> None:
        self._catalog = catalog
        self._timers: dict[str, tuple[float, Callable[[], None]]] = {}
        self._sequence = 0
        self._now = 0.0
        self._text = self._emote = ""
        self._text_id = 0
        self._unshown = False
        self.animation = "idle"
        self.action_id = 0
        self._action_timers: list[str] = []
        self.receive: Callable[[PlaybackEvent], None] = lambda _event: None
        self.player = ReactionPlayer(
            schedule=self.schedule, cancel_timer=self.cancel_timer,
            display_emote=self._display_emote, display_text=self._display_text,
            start_action=lambda clip, _duration: self.play_animation(clip),
            mark_spoken=mark_spoken, is_closed=lambda: False,
            hide_speech=self._hide, social_completed=social_completed,
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
            due = [(token, value) for token, value in self._timers.items()
                   if value[0] <= end]
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
        self._text, self._emote = text, ""
        self._text_id += 1
        self._unshown = True

    def _display_emote(self, emote: str, _milliseconds: int) -> None:
        self._emote, self._text = emote, ""

    def _hide(self) -> None:
        self._text = self._emote = ""
        self._unshown = False

    def acknowledge(self, text_id: int) -> None:
        if text_id == self._text_id:
            self._unshown = False

    def next_text(self) -> None:
        if not self._unshown:
            self.player.advance_story()

    def snapshot(self) -> SpeechSnapshot:
        return SpeechSnapshot(self._text, self._emote, self._text_id,
                              self.player.active, self.player.story_active)

    def speak(
        self, reaction: Reaction | None, *,
        completed: Callable[[bool], None] | None = None,
        subject: str | None = None,
        progress: Callable[[int], bool] | None = None,
    ) -> None:
        self.player.play(reaction, on_complete=completed, subject=subject,
                         on_progress=progress)

    def stop_animation(self) -> None:
        self.action_id += 1
        for token in self._action_timers:
            self.cancel_timer(token)
        self._action_timers.clear()
        self.animation = "idle"

    def play_animation(self, name: str) -> int:
        self.stop_animation()
        self.animation = "pick_up" if name == "hold_item" else name
        clip = self._catalog.clip_for(self.animation, 2)
        action_id = self.action_id
        elapsed = 0
        indices = list(range(len(clip.timings)))
        if name == "hold_item":
            indices = [len(clip.timings) - 1]
        for index in indices:
            source = clip.sprite_index(index)
            events = clip.frames[source].events
            if name == "put_down":
                events = ("detach_object",) if source == 2 else ()
            event = PlaybackEvent(action_id, self.animation, source, events, False)
            self._action_timers.append(self.schedule(
                elapsed, lambda event=event: self.receive(event),
            ))
            elapsed += clip.timings[index]
        final = PlaybackEvent(action_id, self.animation,
                              clip.sprite_index(indices[-1]), (), True)
        self._action_timers.append(self.schedule(
            elapsed, lambda: self.receive(final),
        ))
        return action_id

    def suspend(self) -> None:
        self.player.cancel()
        self.stop_animation()
        self._timers.clear()
        self._hide()
