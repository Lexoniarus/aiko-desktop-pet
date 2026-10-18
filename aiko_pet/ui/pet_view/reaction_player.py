"""Cancellable, Tk-independent playback of immutable authored sequences."""

from __future__ import annotations

from typing import Callable

from ...pet.mind.catalog import Reaction
from ...pet.mind.reaction_sequence import Cue

TimerCallback = Callable[[], None]
ScheduleTimer = Callable[[int, TimerCallback], str]
CancelTimer = Callable[[str], None]
DisplayCue = Callable[[str, int], None]
StartAction = Callable[[str, float], None]


class ReactionPlayer:
    def __init__(
        self,
        *,
        schedule: ScheduleTimer,
        cancel_timer: CancelTimer,
        display_emote: DisplayCue,
        display_text: DisplayCue,
        start_action: StartAction,
        mark_spoken: TimerCallback,
        is_closed: Callable[[], bool],
        hide_speech: TimerCallback = lambda: None,
    ) -> None:
        self._schedule = schedule
        self._cancel_timer = cancel_timer
        self._display_emote = display_emote
        self._display_text = display_text
        self._start_action = start_action
        self._mark_spoken = mark_spoken
        self._is_closed = is_closed
        self._hide_speech = hide_speech
        self._generation = 0
        self._cues: tuple[Cue, ...] = ()
        self._pending_timer: str | None = None
        self._completion: Callable[[bool], None] | None = None
        self._index = -1
        self._story = False
        self._subject: str | None = None

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def cues(self) -> tuple[Cue, ...]:
        return self._cues

    @property
    def pending_timer(self) -> str | None:
        return self._pending_timer

    @property
    def story_active(self) -> bool:
        return self._story and bool(self._cues)

    @property
    def subject(self) -> str | None:
        """The current sequence's subject, cleared with that same lifecycle."""
        return self._subject

    def _invalidate_timer(self) -> None:
        if self._pending_timer is not None:
            self._cancel_timer(self._pending_timer)
            self._pending_timer = None
        self._generation += 1

    def cancel(self) -> None:
        self._invalidate_timer()
        self._cues = ()
        self._story = False
        self._subject = None
        self._index = -1
        self._hide_speech()
        completion, self._completion = self._completion, None
        if completion is not None:
            completion(False)

    def play(
        self,
        reaction: Reaction | None,
        duration_ms: int = 2600,
        *,
        animate: bool = True,
        on_complete: Callable[[bool], None] | None = None,
        subject: str | None = None,
    ) -> None:
        if reaction is None:
            return
        self.cancel()
        self._completion = on_complete
        self._subject = subject
        if animate and reaction.animation != "idle":
            self._start_action(reaction.animation, min(2.0, duration_ms / 1600))
        self._cues = reaction.beats
        self._story = reaction.presentation == "story"
        self._advance(self._generation, 0)

    def advance_story(self) -> bool:
        """Consume one reading click, invalidating even already-queued callbacks."""
        if not self.story_active:
            return False
        self._invalidate_timer()
        index = next(
            (
                i
                for i in range(self._index + 1, len(self._cues))
                if self._cues[i].kind == "text"
            ),
            len(self._cues),
        )
        self._advance(self._generation, index)
        return True

    def _advance(self, generation: int, index: int) -> None:
        if self._is_closed() or generation != self._generation:
            return
        self._pending_timer = None
        if index >= len(self._cues):
            self._complete(generation)
            return
        self._index = index
        cue = self._cues[index]
        if cue.kind == "emote":
            self._display_emote(cue.content, cue.duration_ms)
        elif cue.kind == "text":
            self._display_text(cue.content, cue.duration_ms)
        else:
            self._hide_speech()
        self._mark_spoken()
        self._pending_timer = self._schedule(
            cue.duration_ms,
            lambda: self._advance(generation, index + 1),
        )

    def _complete(self, generation: int) -> None:
        if generation != self._generation:
            return
        self._pending_timer = None
        self._cues = ()
        self._story = False
        self._subject = None
        self._hide_speech()
        completion, self._completion = self._completion, None
        if completion is not None:
            completion(True)
