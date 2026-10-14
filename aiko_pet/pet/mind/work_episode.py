"""Observed work-episode memory for Aiko's grounded dialogue reactions.

No hardware sampling, UI widgets, storage or authored dialogue text. This
component tracks only verified work transitions, interruptions and recovery.
"""

from __future__ import annotations

from .adaptive_models import Behaviour as Behaviour


class WorkEpisodeMemory:
    """Keep short-lived work and recovery context within a single owner."""

    def __init__(self) -> None:
        self.interruptions = 0
        self.last_work_duration = 0.0
        self.recovery_until = -1.0
        self.last_recovery_comment = -1.0
        self.last_work_finished_at = -1.0
        self.postwork_thought_spoken = False

    def observe(
        self,
        previous: Behaviour | None,
        current: Behaviour | None,
        *,
        now: float | None = None,
    ) -> None:
        """React to measured state transitions, never inferred offline work."""
        if current is None:
            self.interruptions = 0
            self.recovery_until = -1.0
        elif previous is not None and previous.focused and not current.focused:
            self.last_work_duration = previous.prolonged_work_seconds
            if now is not None:
                self.recovery_until = now + 110.0
                self.last_work_finished_at = now
                self.postwork_thought_spoken = False
        elif previous is not None and not previous.focused and current.focused:
            # A new work episode cannot inherit interruptions from old work.
            self.interruptions = 0
            self.recovery_until = -1.0
            self.postwork_thought_spoken = False

    def note_click(self, situation: Behaviour | None) -> None:
        """Count interruptions only when verified work is in progress."""
        if situation is not None and situation.focused:
            self.interruptions += 1

    def recovering(self, now: float) -> bool:
        return now < self.recovery_until

    def interpret_event(
        self, event: str, situation: Behaviour | None, now: float,
    ) -> str:
        """Map measured work events to the established dialogue event keys."""
        if event in (
            "computer_effort_rising", "computer_effort_heavy",
            "computer_effort_peak",
        ) and situation is not None:
            if (
                situation.expectation_confident
                and situation.expected_effort is not None
                and situation.expected_effort < 0.3
                and (situation.effort or 0.0) >= 0.5
            ):
                event = "work_unexpected"
        if event.startswith("computer_effort_recovered"):
            if self.interruptions >= 2 and self.last_work_duration >= 18:
                event = "work_finished_interrupted"
            elif self.last_work_duration >= 20 * 60:
                event = "work_finished_long"
            self.recovery_until = now + 110.0
            self.last_recovery_comment = now
            self.last_work_finished_at = now
            self.postwork_thought_spoken = False
            self.interruptions = 0
        return event

    def take_postwork_thought(self, now: float) -> bool:
        """Permit one reflection soon after genuinely prolonged work."""
        if (
            self.last_work_duration < 20 * 60
            or self.postwork_thought_spoken
            or not 60 <= now - self.last_work_finished_at <= 480
        ):
            return False
        self.postwork_thought_spoken = True
        return True
