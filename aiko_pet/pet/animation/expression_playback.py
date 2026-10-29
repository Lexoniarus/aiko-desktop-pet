"""One disposable facial reaction over an already selected frontal rest pose.

No movement, action deadline, dialogue queue or second emotional state lives
here. Loss of a compatible pose consumes the reaction immediately. The latest
prepared mood is projected again only when frontal rest becomes available.
"""

from __future__ import annotations

from dataclasses import replace

from .animation import FrameClock, SpriteSelection
from .character import AnimationClip, CharacterCatalog
from .expression import EXPRESSION_CLIPS, Expression
from .priority import RenderDecision


class ExpressionPlayback:
    def __init__(self, catalog: CharacterCatalog) -> None:
        self._clips = catalog.expression_clips
        self._reaction: Expression | None = None
        self._clock = FrameClock()
        self.compatible = False

    def request(self, expression: Expression | None) -> bool:
        """Reject unavailable reactions at admission, never save them for later."""
        self._reaction = None
        self._clock.reset()
        if (expression is None or not self.compatible
                or EXPRESSION_CLIPS[expression] not in self._clips):
            return False
        self._reaction = expression
        return True

    def select(
        self, base: RenderDecision, now: float, *, mood: Expression,
        blinking: bool,
    ) -> tuple[RenderDecision, bool]:
        """Return presentation plus a receipt when the admitted blink completes."""
        self.compatible = (
            base.sprite.animation == "idle" and base.sprite.fixed_frame in (None, 0)
            and "rest-neutral" in self._clips
        )
        if not self.compatible:
            self.request(None)
            return base, False
        if self._reaction is not None:
            clip = self._clips[EXPRESSION_CLIPS[self._reaction]]
            frame = self._clock.next_index(clip.name, now, clip.timings, loop=False)
            if not self._clock.finished:
                return self._frame(base, clip, frame), False
            self._reaction = None
            self._clock.reset()
        if blinking:
            clip = self._clips["rest-neutral"]
            # AmbientDirector owns the pause between blinks. Preview neutral
            # holds are not added a second time before the actual eye phases.
            order = (2, 3, 4)
            timings = tuple(clip.frames[i].duration_ms for i in order)
            frame = self._clock.next_index("rest-blink", now, timings, loop=False)
            if not self._clock.finished:
                return self._frame(base, clip, order[frame]), False
            self._clock.reset()
            return self._rest(base, mood), True
        self._clock.reset()
        return self._rest(base, mood), False

    def _rest(self, base: RenderDecision, mood: Expression) -> RenderDecision:
        clip = self._clips[EXPRESSION_CLIPS[mood]]
        return self._frame(base, clip, 0 if mood == Expression.NEUTRAL else 1)

    def _frame(
        self, base: RenderDecision, clip: AnimationClip, frame: int,
    ) -> RenderDecision:
        delays = [delay for delay in (
            base.refresh_after_ms, self._clock.next_delay_ms,
        ) if delay is not None]
        # Fixed poses still refresh the continuous sway, independently of the
        # authored reaction/eye hold times and the slower desktop tick.
        return replace(
            base, sprite=SpriteSelection(clip.name, frame),
            refresh_after_ms=min(140, *delays) if delays else 140,
        )
