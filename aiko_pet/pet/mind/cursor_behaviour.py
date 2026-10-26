"""Local cursor interpretation, independent of input, windows and animation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE
from .cursor_attention import CursorPerception

CursorReaction = Literal["ignore", "observe", "approach", "avoid", "flee", "startle"]


@dataclass(frozen=True, slots=True)
class CursorBehaviourContext:
    friendship_level: int
    energy: float
    mood: float
    affection: float = 50.0
    fun: float = 50.0


@dataclass(frozen=True, slots=True)
class CursorIntent:
    reaction: CursorReaction = "ignore"
    side: int = 0
    token: int = 0
    until: float = 0.0
    reason: str = "no-interest"

    @property
    def gaze(self) -> bool:
        return self.reaction != "ignore"

    @property
    def moving(self) -> bool:
        return self.reaction in ("approach", "avoid", "flee")


def parameter(key: str) -> float:
    return BALANCE.number("cursor_behaviour", key)


class CursorBehaviourPolicy:
    """Own one transient response, bounded attempts and their recovery."""

    def __init__(self) -> None:
        self._serial = 0
        self.reset()

    def reset(self) -> None:
        self.current = CursorIntent()
        self.recover_until = 0.0

    def _choose(
        self,
        reaction: CursorReaction,
        side: int,
        now: float,
        seconds: float,
        reason: str,
    ) -> CursorIntent:
        self._serial += 1
        self.current = CursorIntent(reaction, side, self._serial, now + seconds, reason)
        return self.current

    def note_motion_finished(self, token: int, now: float) -> None:
        if self.current.token != token or not self.current.moving:
            return
        self.current = CursorIntent("observe", reason="motion-finished")
        self.recover_until = max(
            self.recover_until,
            now + parameter("attempt_pause_seconds"),
        )

    def evaluate(
        self,
        perception: CursorPerception,
        context: CursorBehaviourContext,
        now: float,
    ) -> CursorIntent:
        p = perception
        if not p.valid or not 0 <= now - p.sampled_at <= 0.5:
            self.reset()
            return self.current
        trust = max(0.0, min(1.0, (context.friendship_level - 1) / 9))
        threat = (
            p.distance < parameter("threat_distance")
            and p.speed > parameter("fast_speed")
            and p.closing_speed > parameter("closing_speed")
        )
        if threat and now >= self.recover_until:
            reaction: CursorReaction = (
                "flee"
                if trust < 0.45 and context.energy >= 25
                else "avoid"
                if context.energy >= 12
                else "startle"
            )
            duration = parameter("flight_seconds") + 1.5 if reaction == "flee" else 2.2
            self.recover_until = now + parameter("recovery_seconds") * (
                1.5 - trust * 0.5
            )
            return self._choose(reaction, -p.side or 1, now, duration, "near-fast-approach")
        if self.current.reaction in ("avoid", "flee", "startle"):
            if now < self.current.until:
                return self.current
        if self.current.reaction == "approach" and now < self.current.until:
            if p.reachable and p.stationary_seconds >= parameter("curiosity_seconds"):
                return self.current
            self.note_motion_finished(self.current.token, now)
        interested = p.distance <= parameter("interest_distance")
        if (
            now >= self.recover_until
            and p.reachable
            and p.side
            and parameter("stop_distance") < p.distance < parameter("approach_distance")
            and p.stationary_seconds >= parameter("curiosity_seconds")
            and context.energy >= 25
            and context.mood >= 30
            and (context.affection <= 75 or context.fun <= 75 or trust > 0.5)
        ):
            return self._choose("approach", p.side, now, 2.5, "calm-reachable-pointer")
        reaction = "observe" if interested and p.stationary_seconds < 8 else "ignore"
        self.current = CursorIntent(
            reaction, reason="watch" if interested else "distant"
        )
        return self.current
