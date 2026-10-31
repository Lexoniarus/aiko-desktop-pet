"""Immutable sleep episodes and pure priorities on the shared elapsed axis."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from .balance import BALANCE


def sleep_setting(name: str) -> float:
    return BALANCE.number("sleep", name)


@dataclass(frozen=True, slots=True)
class SleepEpisode:
    """Durable episode; brief awake care does not create another main sleep."""

    kind: str = ""
    started: float = 0.0
    slept_seconds: float = 0.0
    wake_wall: float = 0.0
    protect_until: float = 0.0
    care_break: bool = False
    search_until: float = 0.0
    intake_until: float = 0.0
    food_failed: bool = False
    failed_food_sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SleepContext:
    """Expected local window plus fresh anonymous input, never hardware load."""

    start_minute: float = sleep_setting("default_start_minute")
    end_minute: float = sleep_setting("default_end_minute")
    idle_seconds: float | None = None
    active_seconds: float = 0.0
    blocked: bool = False
    observed: bool = False

    @classmethod
    def permissions(
        cls,
        bedtime: bool | None,
        nap: bool,
        interrupt: bool,
    ) -> SleepContext:
        return cls(
            idle_seconds=(
                sleep_setting("quiet_seconds")
                if bedtime is True or nap
                else 0.0
                if bedtime is False
                else None
            ),
            active_seconds=sleep_setting("return_seconds") if interrupt else 0.0,
            blocked=bedtime is False and not nap,
            observed=bedtime is not None or nap or interrupt,
        )

    def window(self, wall: float) -> tuple[bool, float, float]:
        local = datetime.fromtimestamp(wall)
        midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
        start = midnight + timedelta(minutes=self.start_minute)
        if local < start:
            start -= timedelta(days=1)
        duration = (self.end_minute - self.start_minute) % 1440
        end = start + timedelta(minutes=duration)
        return start <= local < end, start.timestamp(), end.timestamp()

    def earlier(self, seconds: float) -> SleepContext:
        """Do not project the completed return/idle threshold into its past."""
        if not self.observed:
            return self
        return replace(
            self,
            idle_seconds=max(0, self.idle_seconds - seconds)
            if self.idle_seconds is not None
            else None,
            active_seconds=max(0, self.active_seconds - seconds),
        )

    def unobserved(self) -> SleepContext:
        return SleepContext(self.start_minute, self.end_minute)


@dataclass(frozen=True, slots=True)
class SleepTransition:
    sleeping: bool
    episode: SleepEpisode


def calculate_manual_sleep_transition(
    *,
    sleeping: bool,
    elapsed: float,
    wall: float,
    context: SleepContext,
) -> SleepTransition:
    protection = elapsed + sleep_setting("manual_protection_seconds")
    if sleeping:
        return SleepTransition(False, SleepEpisode(protect_until=protection))
    inside, _, end = context.window(wall)
    kind = "main" if inside else "nap"
    wake = end if inside else wall + sleep_setting("nap_seconds")
    return SleepTransition(True, SleepEpisode(kind, elapsed, 0, wake, protection))


def sleep_transition(
    episode: SleepEpisode,
    *,
    sleeping: bool,
    energy: float,
    elapsed: float,
    wall: float,
    context: SleepContext,
    automatic: bool,
) -> SleepTransition:
    """Evaluate manual grace, recovery, endpoints, return and ordinary sleep."""
    inside, start, end = context.window(wall)
    quiet = context.idle_seconds is not None and context.idle_seconds >= sleep_setting(
        "quiet_seconds"
    )
    if not context.observed:
        quiet = inside and wall >= start + sleep_setting("quiet_seconds")
    active = context.active_seconds >= sleep_setting("return_seconds")
    if elapsed < episode.protect_until:
        return SleepTransition(sleeping, episode)
    if episode.care_break:
        return SleepTransition(False, episode)
    if sleeping:
        # Migrate a legacy sleep without inventing already-slept hours or grace.
        if not episode.kind:
            episode = SleepEpisode(
                "main" if inside else "nap",
                elapsed,
                0,
                end if inside else wall + sleep_setting("nap_seconds"),
            )
        if episode.kind == "nap" and energy <= sleep_setting("exhaustion_energy"):
            episode = replace(episode, kind="recovery")
        if episode.kind == "main":
            wake = wall >= episode.wake_wall and energy >= sleep_setting("wake_energy")
            wake |= (
                active
                and energy >= sleep_setting("early_main_energy")
                and episode.slept_seconds >= sleep_setting("early_main_sleep_seconds")
            )
        elif episode.kind == "recovery":
            wake = energy >= sleep_setting("wake_energy")
            if wake and inside and quiet and automatic:
                return SleepTransition(
                    True, replace(episode, kind="main", wake_wall=end)
                )
        else:
            wake = (
                wall >= episode.wake_wall and energy >= sleep_setting("nap_wake_energy")
            ) or (active and energy >= sleep_setting("nap_wake_energy"))
        if wake:
            return SleepTransition(False, SleepEpisode())
        return SleepTransition(True, episode)
    if not automatic or context.blocked:
        return SleepTransition(False, episode)
    kind = ""
    if energy <= sleep_setting("exhaustion_energy"):
        kind = "recovery"
    elif inside and quiet:
        kind = "main"
    elif not inside and quiet and energy <= sleep_setting("nap_energy"):
        kind = "nap"
    if not kind:
        return SleepTransition(False, episode)
    wake_wall = end if kind == "main" else wall + sleep_setting("nap_seconds")
    return SleepTransition(True, SleepEpisode(kind, elapsed, 0, wake_wall))


def sleep_care_complete(
    episode: SleepEpisode, *, satiety: float, elapsed: float,
) -> bool:
    """One completion rule for reconstructed care and safe live interruption."""
    return episode.care_break and (
        elapsed >= episode.search_until
        or (satiety >= sleep_setting("food_target") and elapsed >= episode.intake_until)
    )
