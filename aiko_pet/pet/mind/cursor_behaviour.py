"""Select bounded cursor encounters; raw motion never commands body animation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from ..balance import BALANCE
from ..interaction_events import CursorExperience
from .cursor_attention import CursorPerception

CursorReaction = Literal["ignore", "observe", "approach", "avoid", "flee", "startle"]
BodyIntent = Literal["front", "three_quarter", "profile"]


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
    target: tuple[int, int] | None = None
    body: BodyIntent = "front"
    strength: int = 0
    experience: CursorExperience | None = None
    steps: int = 1
    attention: float = 0.0
    stage: int = 0

    @property
    def gaze(self) -> bool:
        return self.reaction != "ignore"

    @property
    def moving(self) -> bool:
        return self.reaction in ("approach", "avoid", "flee")


def parameter(key: str) -> float:
    return BALANCE.number("cursor_behaviour", key)


class CursorBehaviourPolicy:
    """One session-scoped episode, fresh evidence, and deliberate body intent."""

    def __init__(self, *, session_id: str | None = None) -> None:
        self._session = session_id or uuid4().hex
        self._serial = 0
        self.reset()

    def reset(self) -> None:
        self.current = CursorIntent()
        self.recover_until = 0.0
        self._encounter = False
        self._retreated = False
        self._access = False
        self._outside_since: float | None = None
        self._calm_since: float | None = None
        self._calm_side = 0
        self._last_sample = -100.0
        self.attention = 0.0
        self.stage = 0
        self._release = [0.0, 0.0, 0.0]
        self._selected_at = -100.0
        self._look_until = 0.0
        self._curiosity_level = 0
        self._fear_level = 0
        self._trust = 0.0
        self._willing = False

    def suspend(self, now: float) -> None:
        """Yield attention to a real activity without rearming an escape."""
        self.note_motion_finished(self.current.token, now)
        self._clear_attention()
        self.current = CursorIntent(reason="activity")

    def claim_access(self, now: float) -> None:
        """Contact owns input; a lingering impression cannot restart this attempt."""
        self._clear_attention()
        self._access = True
        self.note_motion_finished(self.current.token, now)
        self.current = CursorIntent(reason="direct-access")

    def note_motion_finished(self, token: int, now: float) -> None:
        if self.current.token != token or not self.current.moving:
            return
        self.recover_until = max(
            self.recover_until,
            now
            + (
                parameter("attempt_pause_seconds")
                if self.current.reaction == "approach"
                else parameter("recovery_seconds")
            ),
        )
        self.current = replace(
            self.current,
            reaction="observe",
            body="front",
            until=now + 2,
            experience=None,
            reason="motion-finished",
        )
        self._look_until = now + 2

    def _clear_attention(self) -> None:
        self.attention, self.stage = 0.0, 0
        self._release = [0.0, 0.0, 0.0]
        self._last_sample = -100.0
        self._calm_since = None

    def _integrate(self, p: CursorPerception, dt: float) -> None:
        band = p.motion_band
        far = p.distance > parameter("interest_distance")
        rates = {
            "still": -parameter("still_loss_per_second"),
            "slow": -parameter("slow_loss_per_second"),
            "normal": parameter("normal_gain"),
            "fast": parameter("fast_gain"),
            "very_fast": parameter("very_fast_gain"),
        }
        rate = rates[band]
        if far and rate > 0:
            cap = parameter("far_attention_cap")
            self.attention = (
                max(cap, self.attention - parameter("slow_loss_per_second") * dt)
                if self.attention > cap else min(cap, self.attention + 4 * dt)
            )
        else:
            self.attention = max(0.0, min(100.0, self.attention + rate * dt))
        for level, key in enumerate(("noticed_at", "focused_at", "strong_at"), 1):
            if self.attention >= parameter(key):
                self.stage = max(self.stage, level)
        for index, key in enumerate((
            "gaze_release_below", "body_release_below", "strong_release_below",
        )):
            self._release[index] = (
                self._release[index] + dt if self.attention < parameter(key) else 0.0
            )
            if self._release[index] + 1e-9 >= parameter("release_hold_seconds"):
                self.stage = min(self.stage, index)

    def _evidence(
        self, feeling: Literal["curiosity", "fear"], level: int
    ) -> CursorExperience:
        return CursorExperience(
            f"{self._session}:{self._serial}:{feeling}:{level}", feeling, level
        )

    def evaluate(
        self, perception: CursorPerception, context: CursorBehaviourContext, now: float
    ) -> CursorIntent:
        p = perception
        self.current = replace(self.current, experience=None)
        if not p.valid or not 0 <= now - p.sampled_at <= 0.5:
            self.note_motion_finished(self.current.token, now)
            self._calm_since = None
            self._last_sample = -100.0
            self.current = CursorIntent(reason="invalid-sample")
            return self.current
        dt = p.sampled_at - self._last_sample
        if dt == 0:
            return self.current
        continuous = 0 < dt <= 1.5
        self._last_sample = p.sampled_at
        self._integrate(p, dt if continuous else 0.0)
        if p.distance > parameter("interest_distance"):
            self._calm_since = None
            if self._outside_since is None:
                self._outside_since = now
            if now - self._outside_since >= parameter("encounter_release_seconds"):
                self._encounter = False
                self._retreated = False
                self._access = False
            self.current = CursorIntent(
                "observe" if self.stage else "ignore", target=p.pointer,
                attention=self.attention, stage=self.stage, reason="distant",
            )
            return self.current
        self._outside_since = None
        if not self._encounter:
            self._encounter = True
            self._serial += 1
            self._trust = max(0, min(1, (context.friendship_level - 1) / 9))
            self._willing = (
                context.energy >= 25
                and context.mood >= 30
                and (context.affection <= 75 or context.fun <= 75 or self._trust > 0.5)
            )
            self._look_until = now + 3
            self._selected_at = now
            self.current = CursorIntent(
                "observe", token=self._serial, until=self._look_until, target=p.pointer
            )
        threat = (
            p.distance < parameter("threat_distance")
            and p.speed > parameter("fast_speed")
            and p.closing_speed > parameter("closing_speed")
        )
        if (
            threat
            and not self._retreated
            and not self._access
            and now >= self.recover_until
        ):
            self._retreated = True
            level = min(3, max(1, round(3 - 2 * self._trust + (context.energy < 25))))
            self._fear_level = level
            reaction: CursorReaction = (
                "flee"
                if self._trust < 0.45 and context.energy >= 25
                else "avoid"
                if context.energy >= 12
                else "startle"
            )
            self._look_until = now + 3
            self.recover_until = now + parameter("recovery_seconds")
            self.current = CursorIntent(
                reaction,
                -p.side or 1,
                self._serial * 4 + 2,
                now + 15,
                "near-fast-approach",
                p.pointer,
                "front" if reaction == "startle" else "profile",
                level,
                self._evidence("fear", level),
            )
            return self.current
        if self.current.moving:
            if now < self.current.until:
                return self.current
            self.note_motion_finished(self.current.token, now)
        if self.current.reaction == "startle" and now < self._look_until:
            return self.current
        calm = p.speed <= parameter("calm_speed") and p.side != 0
        if not calm or self._calm_side != p.side or not continuous:
            self._calm_since = now if calm else None
            self._calm_side = p.side
        elif self._calm_since is None:
            self._calm_since = now
        duration = 0 if self._calm_since is None else now - self._calm_since
        experience = None
        if (
            duration >= parameter("curiosity_seconds")
            and not self._access
            and not self._retreated
            and p.distance <= parameter("approach_distance")
        ):
            # Strength is frozen from actual encounter context, never moodlet feedback.
            level = (
                1 + int(self._trust >= 0.4) + int(self._trust >= 0.8 and self._willing)
            )
            if level > self._curiosity_level:
                self._curiosity_level = level
                experience = self._evidence("curiosity", level)
        engaged = self._curiosity_level > 0 and calm and not self._retreated
        body: BodyIntent = (
            "three_quarter"
            if engaged
            and duration >= parameter("body_interest_seconds")
            and not self._access
            else "front"
        )
        reaction = "observe" if self.stage else "ignore"
        until = now + 2 if engaged else self._look_until
        if (
            not self._access
            and not self._retreated
            and self._willing
            and now >= self.recover_until
            and engaged
            and p.reachable
            and parameter("stop_distance") < p.distance < parameter("approach_distance")
            and duration >= parameter("approach_wait_seconds")
        ):
            reaction, body, until = "approach", "profile", now + 15
        target = p.pointer if self.stage else None
        self.current = CursorIntent(
            reaction,
            p.side if body != "front" else 0,
            self._serial * 4 + 1 if reaction == "approach" else self._serial * 4,
            until,
            "calm-interest" if engaged else "brief-look",
            target,
            body,
            self._curiosity_level,
            experience,
            2 if self._trust >= 0.7 else 1,
            self.attention,
            self.stage,
        )
        return self.current
