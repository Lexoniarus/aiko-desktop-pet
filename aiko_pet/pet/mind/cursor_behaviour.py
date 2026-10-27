"""Select bounded cursor encounters; raw motion never commands body animation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from ..balance import BALANCE
from ..interaction_events import CursorExperience, CursorWarning, CursorWarningReceipt
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
    warning: CursorWarning | None = None

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
        self._motion_serial = 0
        self._warning_serial = 0
        self._last_warning_at = -100.0
        self.reset()

    def reset(self) -> None:
        self.current = CursorIntent()
        self.recover_until = 0.0
        self._encounter = False
        self._retreated = False
        self._access = False
        self._outside_since: float | None = None
        self._positive_since: float | None = None
        self._last_sample = -100.0
        self.attention = 0.0
        self.stage = 0
        self._release = [0.0, 0.0, 0.0]
        self._side_samples: deque[tuple[float, float, int]] = deque()
        self._body_side = 0
        self._opposite_seconds = 0.0
        self._far_seconds = 0.0
        self._look_until = 0.0
        self._curiosity_level = 0
        self._fear_level = 0
        self._trust = 0.0
        self._willing = False
        self._pending_warning: CursorWarning | None = None
        self._warned_at: float | None = None
        self._threat_active = False

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
        self._positive_since = None
        self._side_samples.clear()
        self._body_side = 0
        self._opposite_seconds = self._far_seconds = 0.0
        self._pending_warning = None
        self._warned_at = None
        self._threat_active = False

    def note_warning(self, receipt: CursorWarningReceipt) -> None:
        """Consume a matching, fresh display receipt without advancing pet time."""
        pending = self._pending_warning
        if (pending is None or receipt.warning_id != pending.warning_id
                or not 0 <= receipt.presented_at - pending.created_at
                <= parameter("warning_candidate_seconds")):
            return
        self._pending_warning = None
        if receipt.presented:
            self._warned_at = receipt.presented_at
            self._last_warning_at = receipt.presented_at

    def _orient_body(self, p: CursorPerception, dt: float) -> None:
        if dt == 0 or self.stage == 0 or self._access:
            self._side_samples.clear()
            self._body_side = 0
            self._opposite_seconds = self._far_seconds = 0.0
            return
        far = p.distance > parameter("interest_distance")
        self._far_seconds = self._far_seconds + dt if far else 0.0
        if self.stage < 2 or self._far_seconds >= parameter("release_hold_seconds"):
            self._body_side = 0
        cutoff = p.sampled_at - parameter("side_window_seconds")
        self._side_samples.append((
            p.sampled_at - dt, p.sampled_at, p.side if not far else 0,
        ))
        while self._side_samples and self._side_samples[0][1] <= cutoff:
            self._side_samples.popleft()
        if self._body_side:
            self._opposite_seconds = (
                self._opposite_seconds + dt if p.side == -self._body_side else 0.0
            )
            if self._opposite_seconds + 1e-9 >= parameter("opposite_hold_seconds"):
                self._body_side = 0
                self._side_samples.clear()
                self._opposite_seconds = 0.0
            return
        if self.attention < parameter("focused_at") or far or p.side == 0:
            return
        held = sum(end - max(start, cutoff) for start, end, side in self._side_samples
                   if side == p.side)
        if held + 1e-9 >= parameter("side_required_seconds"):
            self._body_side = p.side

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
        self.current = replace(self.current, experience=None, warning=None)
        if not p.valid or not 0 <= now - p.sampled_at <= 0.5:
            self.note_motion_finished(self.current.token, now)
            self._positive_since = None
            self._last_sample = -100.0
            self._pending_warning = None
            self._warned_at = None
            self._threat_active = False
            self.current = CursorIntent(reason="invalid-sample")
            return self.current
        dt = p.sampled_at - self._last_sample
        if dt == 0:
            return self.current
        continuous = 0 < dt <= 1.5
        self._last_sample = p.sampled_at
        self._integrate(p, dt if continuous else 0.0)
        self._orient_body(p, dt if continuous else 0.0)
        if p.distance > parameter("interest_distance"):
            self._threat_active = False
            self._pending_warning = None
            self._warned_at = None
            self._positive_since = None
            if self._outside_since is None:
                self._outside_since = now
            if now - self._outside_since >= parameter("encounter_release_seconds"):
                self._encounter = False
                self._retreated = False
                self._access = False
            self.current = CursorIntent(
                "observe" if self.stage else "ignore", target=p.pointer,
                attention=self.attention, stage=self.stage, reason="distant",
                side=self._body_side,
                body="three_quarter" if self._body_side else "front",
            )
            return self.current
        self._outside_since = None
        if not self._encounter:
            self._encounter = True
            self._serial += 1
            self._curiosity_level = self._fear_level = 0
            self._trust = max(0, min(1, (context.friendship_level - 1) / 9))
            self._willing = (
                context.energy >= 25
                and context.mood >= 30
                and (context.affection <= 75 or context.fun <= 75 or self._trust > 0.5)
            )
            self._look_until = now + 3
            self.current = CursorIntent(
                "observe", token=self._serial, until=self._look_until, target=p.pointer
            )
        threat = (
            p.distance <= parameter("warning_distance")
            and p.speed >= parameter("warning_speed")
            and p.closing_speed >= parameter("warning_closing_speed")
            and p.motion_band not in ("still", "slow")
        )
        new_approach = threat and not self._threat_active
        self._threat_active = threat
        warning = None
        if (new_approach and not self._retreated and not self._access
                and now >= self.recover_until):
            warned = self._warned_at
            if (warned is not None and warned < p.sampled_at
                    <= warned + parameter("warning_window_seconds")):
                self._motion_serial += 1
                self._retreated = True
                level = min(3, max(1, round(
                    3 - 2 * self._trust + (context.energy < 25)
                )))
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
                    self._motion_serial,
                    now + 15,
                    "near-fast-approach",
                    p.pointer,
                    "front" if reaction == "startle" else "profile",
                    level,
                    self._evidence("fear", level),
                )
                return self.current
            if now - self._last_warning_at >= parameter("warning_repeat_seconds"):
                self._warning_serial += 1
                warning = CursorWarning(
                    f"{self._session}:{self._serial}:warning:{self._warning_serial}",
                    now,
                )
                self._pending_warning = warning
                # A warning may briefly orient the head without earning a moodlet.
                self.attention = max(self.attention, parameter("noticed_at"))
                self.stage = max(1, self.stage)
        if self.current.moving:
            if (now < self.current.until and not (
                    self.current.reaction == "approach"
                    and (not p.reachable or p.side != self.current.side))):
                self.current = replace(
                    self.current, target=p.pointer,
                    attention=self.attention, stage=self.stage,
                )
                return self.current
            self.note_motion_finished(self.current.token, now)
        if self.current.reaction == "startle" and now < self._look_until:
            return self.current
        positive = (
            continuous and self.attention >= parameter("strong_at")
            and p.motion_band in ("normal", "fast", "very_fast")
            and not threat and not self._retreated and not self._access
        )
        if not positive:
            self._positive_since = None
        elif self._positive_since is None:
            self._positive_since = p.sampled_at
        duration = (0.0 if self._positive_since is None
                    else p.sampled_at - self._positive_since)
        qualified = duration + 1e-9 >= parameter("positive_observation_seconds")
        experience = None
        if qualified:
            # Encounter context is frozen before its own moodlet can feed back.
            level = (
                1 + int(self._trust >= 0.4) + int(self._trust >= 0.8 and self._willing)
            )
            if level > self._curiosity_level:
                self._curiosity_level = level
                experience = self._evidence("curiosity", level)
        engaged = positive and self._curiosity_level > 0
        body: BodyIntent = "three_quarter" if self._body_side else "front"
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
            and self._body_side == p.side and p.side != 0
        ):
            self._motion_serial += 1
            reaction, body, until = "approach", "profile", now + 15
        target = p.pointer if self.stage else None
        self.current = CursorIntent(
            reaction,
            p.side if body == "profile" else self._body_side,
            self._motion_serial if reaction == "approach" else self._serial * 4,
            until,
            "observed-interest" if engaged else "attention",
            target,
            body,
            self._curiosity_level,
            experience,
            2 if self._trust >= 0.7 else 1,
            self.attention,
            self.stage,
            warning,
        )
        return self.current
