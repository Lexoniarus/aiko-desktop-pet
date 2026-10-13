"""Hardware-effort narrative, separate from Aiko's conversation decisions.

ComputerVoice classifies observed load into authored event keys. It does not
sample hardware, render text, infer applications or send telemetry anywhere.
"""

from __future__ import annotations

import random

from .telemetry import ComputerSnapshot, workload_intensity

class ComputerVoice:
    """Translate measured effort into Aiko's *subjective* working rhythm.

    CPU/GPU/RAM are inputs only. Speech never identifies a component or an
    imagined task. A proper 'that was hard' response requires sustained load.
    """

    MIN_SECONDS_BETWEEN = 370.0
    MIN_CHANGE_SECONDS = 18.0
    STRESS_SECONDS = 18.0

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
        if snapshot.measured_at <= 0 or now - snapshot.measured_at > 25:
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
        if current >= 0.70:
            self._last_high_at = now
            if self._stressed_since is None:
                self._stressed_since = now
                self._peak_effort = current
                self._milestone_spoken = False
            self._peak_effort = max(self._peak_effort, current)
            duration = now - self._stressed_since
            if duration >= self.STRESS_SECONDS and not self._milestone_spoken:
                self._milestone_spoken = True
                event = ("computer_effort_peak" if self._peak_effort >= 0.90
                         else "computer_effort_heavy")
        elif self._stressed_since is not None:
            duration = now - self._stressed_since
            was_recent = (
                self._last_high_at is not None
                and now - self._last_high_at <= 90
            )
            if current < 0.42 and duration >= self.STRESS_SECONDS and was_recent:
                event = ("computer_effort_recovered_peak"
                         if self._peak_effort >= 0.90
                         else "computer_effort_recovered")
            elif current < 0.42 and duration >= 7:
                event = "computer_effort_easing"
            if current < 0.42 or not was_recent:
                self._stressed_since = None
                self._peak_effort = 0.0
                self._milestone_spoken = False
                self._last_high_at = None
        if event is None and before is not None:
            if current - before >= 0.23 and current >= 0.32:
                event = "computer_effort_rising"
            elif before - current >= 0.27 and current < 0.55:
                event = "computer_effort_easing"
        elif event is None and before is None and current >= 0.70:
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
        if effort >= 0.70:
            return "computer_effort_steady"
        if effort <= 0.20:
            return "computer_effort_rest"
        if snapshot.uptime_hours is not None and snapshot.uptime_hours >= 8:
            return "computer_uptime"
        return None

    def maybe_event(self, snapshot: "ComputerSnapshot", now: float) -> str | None:
        since_last = now - max(self.last_voice_at, self.last_change_at)
        if since_last < self.MIN_SECONDS_BETWEEN:
            return None
        if snapshot.measured_at <= 0 or now - snapshot.measured_at > 65:
            return None
        event = self.classify(snapshot)
        if event is None:
            return None
        if event == "computer_effort_rest" and (snapshot.uptime_hours or 0) >= 8:
            if self.rng.random() < 0.18:
                event = "computer_uptime"
        if self.rng.random() >= (0.56 if event == "computer_effort_steady" else 0.25):
            return None
        self.last_voice_at = now
        return event
