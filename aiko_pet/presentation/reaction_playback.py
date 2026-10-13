"""Tk-independent timing and cancellation for Aiko's visual reactions.

The playback controller owns every reaction-generation guard and its scheduled
follow-up. The GUI supplies the Tk scheduler and presentation callbacks.
"""

from __future__ import annotations

from typing import Callable

from ..personality.catalog import Reaction
from ..personality.reaction_sequence import Cue, compose_cues

TimerCallback = Callable[[], None]
ScheduleTimer = Callable[[int, TimerCallback], str]
CancelTimer = Callable[[str], None]
DisplayCue = Callable[[str, int], None]
StartAction = Callable[[str, float], None]


def choose_idle_emote(
    *, energy: float, satiety: float, mood: float, affection: float,
) -> str:
    """Select the original need-dependent idle icon in priority order."""
    if energy < 20:
        return "sleeps"
    if satiety < 18:
        return "drops"
    if mood < 18:
        return "faceSad"
    if affection < 18:
        return "heart"
    if mood > 88:
        return "star"
    return "idea"


class ReactionPlayer:
    """Play non-overlapping reaction cues, cancelling stale queued callbacks."""

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
    ) -> None:
        self._schedule = schedule
        self._cancel_timer = cancel_timer
        self._display_emote = display_emote
        self._display_text = display_text
        self._start_action = start_action
        self._mark_spoken = mark_spoken
        self._is_closed = is_closed
        self._generation = 0
        self._cues: tuple[Cue, ...] = ()
        self._pending_timer: str | None = None

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def cues(self) -> tuple[Cue, ...]:
        return self._cues

    @property
    def pending_timer(self) -> str | None:
        return self._pending_timer

    def cancel(self) -> None:
        """Invalidate callbacks and remove an existing reaction timer."""
        if self._pending_timer is not None:
            self._cancel_timer(self._pending_timer)
            self._pending_timer = None
        self._generation += 1
        self._cues = ()

    def play(
        self,
        reaction: Reaction | None,
        duration_ms: int = 2600,
        *,
        animate: bool = True,
    ) -> None:
        """Start a fresh reaction while preserving original event ordering."""
        if reaction is None:
            return
        self.cancel()
        generation = self._generation
        if animate and reaction.animation != "idle":
            self._start_action(reaction.animation, min(2.0, duration_ms / 1600))
        self._mark_spoken()
        if reaction.emote_before is not None or reaction.emote_after is not None:
            self._cues = compose_cues(
                reaction.text,
                before=reaction.emote_before,
                followup=reaction.followup_text,
                after=reaction.emote_after,
                minimum_text_ms=max(1700, duration_ms - 500),
            )
            self._advance(generation, 0)
            return
        # Ordinary speech retains its shorter, deliberately awkward follow-up.
        self._display_text(
            reaction.text,
            max(duration_ms, reaction.followup_delay_ms + 200),
        )
        followup_text = reaction.followup_text
        if followup_text:
            self._pending_timer = self._schedule(
                reaction.followup_delay_ms,
                lambda: self._show_followup(generation, followup_text),
            )

    def _advance(self, generation: int, index: int) -> None:
        """Render precisely one cue, never emote and text simultaneously."""
        self._pending_timer = None
        if self._is_closed() or generation != self._generation:
            return
        if index >= len(self._cues):
            self._cues = ()
            return
        cue = self._cues[index]
        if cue.kind == "emote":
            self._display_emote(cue.content, cue.duration_ms)
        else:
            self._display_text(cue.content, cue.duration_ms)
        self._mark_spoken()
        if index + 1 < len(self._cues):
            self._pending_timer = self._schedule(
                cue.duration_ms,
                lambda: self._advance(generation, index + 1),
            )
        else:
            self._pending_timer = self._schedule(
                cue.duration_ms,
                lambda: self._complete(generation),
            )

    def _complete(self, generation: int) -> None:
        self._pending_timer = None
        if generation == self._generation:
            self._cues = ()

    def _show_followup(self, generation: int, text: str) -> None:
        self._pending_timer = None
        if self._is_closed() or generation != self._generation:
            return
        self._display_text(text, 2600)
        self._mark_spoken()
