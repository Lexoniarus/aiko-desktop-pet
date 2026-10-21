"""Cancellable, Tk-independent playback of immutable authored sequences."""

from __future__ import annotations

from typing import Callable

from ...pet.interaction_events import SocialCompletion
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
        on_text: Callable[[str], None] = lambda _event: None,
        on_wish_text: Callable[[int], None] = lambda _instance: None,
        social_completed: Callable[[SocialCompletion], None] = lambda _kind: None,
    ) -> None:
        self._on_text = on_text
        self._social_completed = social_completed
        self._on_wish_text = on_wish_text
        self._wish_instance_id: int | None = None
        self._completed_social: SocialCompletion | None = None
        self._text_reported = False
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
        self._event: str | None = None
        self._incidental = False

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
    def active(self) -> bool:
        """A short reaction or story still owns its authored playback sequence."""
        return bool(self._cues)

    @property
    def story_active(self) -> bool:
        return self._story and bool(self._cues)

    @property
    def subject(self) -> str | None:
        """The current sequence's subject, cleared with that same lifecycle."""
        return self._subject

    @property
    def event(self) -> str | None:
        """Semantic event of the current sequence, with the same lifecycle."""
        return self._event

    @property
    def interruptible(self) -> bool:
        """Only incidental speech/click replies yield to deliberate interaction."""
        event = self._event or ""
        return self.active and not self.story_active and (
            self._incidental or event.startswith("click_")
            or event in ("rapid_click", "sleep_click")
        )

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
        self._event = None
        self._incidental = False
        self._wish_instance_id = None
        self._completed_social = None
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
        incidental: bool = False,
    ) -> None:
        if reaction is None:
            return
        self.cancel()
        self._completion = on_complete
        self._subject = subject
        self._event = reaction.event
        self._incidental = incidental
        self._wish_instance_id = reaction.wish_instance_id
        self._completed_social = reaction.completed_social
        self._text_reported = False
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
            if not self._text_reported and self._event is not None:
                self._text_reported = True
                wish_instance_id = self._wish_instance_id
                self._on_text(self._event)
                if wish_instance_id is not None:
                    self._on_wish_text(wish_instance_id)
        else:
            self._hide_speech()
        if generation != self._generation:
            return
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
        self._event = None
        self._incidental = False
        self._wish_instance_id = None
        social, self._completed_social = self._completed_social, None
        self._hide_speech()
        completion, self._completion = self._completion, None
        if completion is not None:
            completion(True)
        if social is not None:
            self._social_completed(social)
