"""Hardware-effort narrative, separate from Aiko's conversation decisions.

WorkloadEventDetector classifies observed load into authored event keys. It does not
sample hardware, render text, infer applications or send telemetry anywhere.
"""

from __future__ import annotations

from ..balance import BALANCE

import random

from ...telemetry import ComputerSnapshot, workload_intensity


class WorkloadEventDetector:
    """Translate measured effort into Aiko's *subjective* working rhythm.

    CPU/GPU/RAM are inputs only. Speech never identifies a component or an
    imagined task. A proper 'that was hard' response requires sustained load.
    """

    MIN_SECONDS_BETWEEN = BALANCE.number(
        "workload_dialogue", "minimum_voice_interval_seconds"
    )
    MIN_CHANGE_SECONDS = BALANCE.number("workload_dialogue", "minimum_change_seconds")
    STRESS_SECONDS = BALANCE.number("workload_dialogue", "stress_seconds")

    def __init__(self, *, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.last_voice_at = float("-inf")
        self.last_change_at = float("-inf")
        self._last_sample: ComputerSnapshot | None = None
        self._stressed_since: float | None = None
        self._peak_effort = 0.0
        self._milestone_spoken = False
        self._last_high_at: float | None = None

    def reset_samples(self) -> None:
        self._last_sample = None
        self._stressed_since = None
        self._peak_effort = 0.0
        self._milestone_spoken = False
        self._last_high_at = None

    def observe_change(self, snapshot: ComputerSnapshot, now: float) -> str | None:
        """Emit meaningful transitions only once per fresh hardware reading."""
        if snapshot.measured_at <= 0 or now - snapshot.measured_at > BALANCE.integer(
            "workload_dialogue", "change_sample_maximum_age_seconds"
        ):
            return None
        previous = self._last_sample
        if previous is not None and snapshot.measured_at <= previous.measured_at:
            return None
        self._last_sample = snapshot
        current = workload_intensity(snapshot)
        if current is None:
            self._stressed_since = None
            self._peak_effort = 0.0
            self._milestone_spoken = False
            self._last_high_at = None
            return None
        before = workload_intensity(previous) if previous is not None else None
        event: str | None = None
        if current >= BALANCE.number("workload_dialogue", "high_effort"):
            self._last_high_at = now
            if self._stressed_since is None:
                self._stressed_since = now
                self._peak_effort = current
                self._milestone_spoken = False
            self._peak_effort = max(self._peak_effort, current)
            duration = now - self._stressed_since
            if duration >= self.STRESS_SECONDS and not self._milestone_spoken:
                self._milestone_spoken = True
                event = (
                    "computer_effort_peak"
                    if self._peak_effort
                    >= BALANCE.number("workload_dialogue", "peak_effort")
                    else "computer_effort_heavy"
                )
        elif self._stressed_since is not None:
            duration = now - self._stressed_since
            was_recent = (
                self._last_high_at is not None
                and now - self._last_high_at
                <= BALANCE.integer("workload_dialogue", "recent_high_seconds")
            )
            if (
                current < BALANCE.number("workload_dialogue", "recovered_effort")
                and duration >= self.STRESS_SECONDS
                and was_recent
            ):
                event = (
                    "computer_effort_recovered_peak"
                    if self._peak_effort
                    >= BALANCE.number("workload_dialogue", "peak_effort")
                    else "computer_effort_recovered"
                )
            elif current < BALANCE.number(
                "workload_dialogue", "recovered_effort"
            ) and duration >= BALANCE.integer(
                "workload_dialogue", "minimum_short_work_seconds"
            ):
                event = "computer_effort_easing"
            if (
                current < BALANCE.number("workload_dialogue", "recovered_effort")
                or not was_recent
            ):
                self._stressed_since = None
                self._peak_effort = 0.0
                self._milestone_spoken = False
                self._last_high_at = None
        if event is None and before is not None:
            if current - before >= BALANCE.number(
                "workload_dialogue", "rise_delta"
            ) and current >= BALANCE.number("workload_dialogue", "rise_minimum_effort"):
                event = "computer_effort_rising"
            elif before - current >= BALANCE.number(
                "workload_dialogue", "fall_delta"
            ) and current < BALANCE.number("workload_dialogue", "fall_maximum_effort"):
                event = "computer_effort_easing"
        elif (
            event is None
            and before is None
            and current >= BALANCE.number("workload_dialogue", "high_effort")
        ):
            event = "computer_effort_rising"
        if event is None:
            return None
        # Recovery after hard work is a meaningful ending, even if her earlier
        # remark was recent. All other transitions respect the quiet period.
        recovery = event.startswith("computer_effort_recovered")
        if not recovery and now - self.last_change_at < self.MIN_CHANGE_SECONDS:
            return None
        self.last_change_at = now
        return event

    @staticmethod
    def classify(snapshot: "ComputerSnapshot") -> str | None:
        if not isinstance(snapshot, ComputerSnapshot):
            return None
        effort = workload_intensity(snapshot)
        if effort is None:
            return None
        if effort >= BALANCE.number("workload_dialogue", "high_effort"):
            return "computer_effort_steady"
        if effort <= BALANCE.number("workload_dialogue", "rest_effort"):
            return "computer_effort_rest"
        if (
            snapshot.uptime_hours is not None
            and snapshot.uptime_hours
            >= BALANCE.integer("workload_dialogue", "long_uptime_hours")
        ):
            return "computer_uptime"
        return None

    def maybe_event(self, snapshot: "ComputerSnapshot", now: float) -> str | None:
        since_last = now - max(self.last_voice_at, self.last_change_at)
        if since_last < self.MIN_SECONDS_BETWEEN:
            return None
        if snapshot.measured_at <= 0 or now - snapshot.measured_at > BALANCE.integer(
            "workload_dialogue", "voice_sample_maximum_age_seconds"
        ):
            return None
        event = self.classify(snapshot)
        if event is None:
            return None
        if event == "computer_effort_rest" and (
            snapshot.uptime_hours or 0
        ) >= BALANCE.integer("workload_dialogue", "long_uptime_hours"):
            if self.rng.random() < BALANCE.number(
                "workload_dialogue", "long_uptime_comment_probability"
            ):
                event = "computer_uptime"
        if self.rng.random() >= (
            BALANCE.number("workload_dialogue", "steady_silence_probability")
            if event == "computer_effort_steady"
            else BALANCE.number("workload_dialogue", "other_silence_probability")
        ):
            return None
        self.last_voice_at = now
        return event
