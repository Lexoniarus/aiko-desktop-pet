"""Observed work-episode memory for Aiko's grounded dialogue reactions.

No hardware sampling, UI widgets, storage or authored dialogue text. This
component tracks only verified work transitions, interruptions and recovery.
"""

from __future__ import annotations

from ..balance import BALANCE
from .adaptive_models import Behaviour


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
                self.recovery_until = now + BALANCE.number(
                    "work_episode", "recovery_seconds"
                )
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
        self,
        event: str,
        situation: Behaviour | None,
        now: float,
    ) -> str:
        """Map measured work events to the established dialogue event keys."""
        if (
            event
            in (
                "computer_effort_rising",
                "computer_effort_heavy",
                "computer_effort_peak",
            )
            and situation is not None
        ):
            if (
                situation.expectation_confident
                and situation.expected_effort is not None
                and situation.expected_effort
                < BALANCE.number("work_episode", "unexpected_work_expected_effort")
                and (situation.effort or 0.0)
                >= BALANCE.number("work_episode", "unexpected_work_measured_effort")
            ):
                event = "work_unexpected"
        if event.startswith("computer_effort_recovered"):
            if self.interruptions >= BALANCE.integer(
                "work_episode", "interruption_count"
            ) and self.last_work_duration >= BALANCE.integer(
                "work_episode", "minimum_interrupted_work_seconds"
            ):
                event = "work_finished_interrupted"
            elif self.last_work_duration >= BALANCE.integer(
                "work_episode", "prolonged_work_seconds"
            ):
                event = "work_finished_long"
            self.recovery_until = now + BALANCE.number(
                "work_episode", "recovery_seconds"
            )
            self.last_recovery_comment = now
            self.last_work_finished_at = now
            self.postwork_thought_spoken = False
            self.interruptions = 0
        return event

    def take_postwork_thought(self, now: float) -> bool:
        """Permit one reflection soon after genuinely prolonged work."""
        if (
            self.last_work_duration
            < BALANCE.integer("work_episode", "prolonged_work_seconds")
            or self.postwork_thought_spoken
            or not BALANCE.integer("work_episode", "minimum_followup_seconds")
            <= now - self.last_work_finished_at
            <= BALANCE.integer("work_episode", "maximum_followup_seconds")
        ):
            return False
        self.postwork_thought_spoken = True
        return True
