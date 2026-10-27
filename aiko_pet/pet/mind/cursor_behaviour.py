"""Select bounded cursor encounters; raw motion never commands body animation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from ..balance import BALANCE
from ..cursor_experiences import CursorFeeling
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
    cursor_feeling: CursorFeeling | None = None
    cursor_level: int = 0


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
    feeling: CursorFeeling | None = None
    running: bool = False

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
        self._evidence_serial = 0
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
        self._play_seconds = 0.0
        self._last_play_at = -100.0
        self._last_curiosity_evidence = -100.0
        self._play_rate = 1.0
        self._fear_level = 0
        self._trust = 0.0
        self._willing = False
        self._pending_warning: CursorWarning | None = None
        self._warned_at: float | None = None
        self._threat_active = False
        self._known_feeling: CursorFeeling | None = None

    def suspend(self, now: float) -> None:
        """Yield attention to a real activity without rearming an escape."""
        self.note_motion_finished(self.current.token, now)
        self._clear_attention(clear_score=False)
        self.current = CursorIntent(
            reason="activity", attention=self.attention, stage=self.stage,
        )

    def claim_access(self, now: float) -> None:
        """Contact owns input; a lingering impression cannot restart this attempt."""
        self._clear_attention()
        self._access = True
        self.note_motion_finished(self.current.token, now)
        self.current = CursorIntent(reason="direct-access")

    def pause_for_menu(
        self, perception: CursorPerception, now: float,
        *, feeling: CursorFeeling | None = None,
    ) -> None:
        """Hold interest and gaze during real control use, without new feelings."""
        self.note_motion_finished(self.current.token, now)
        fresh = perception.valid and 0 <= now - perception.sampled_at <= 0.5
        self._last_sample = perception.sampled_at if fresh else -100.0
        self._positive_since = None
        self._last_play_at = -100.0
        self._side_samples.clear()
        self._opposite_seconds = self._far_seconds = 0.0
        self._pending_warning = None
        self._warned_at = None
        self._threat_active = False
        self.current = replace(
            self.current, reaction="observe" if self.stage else "ignore",
            target=perception.pointer if fresh else self.current.target,
            body="three_quarter" if self._body_side else "front", side=self._body_side,
            attention=self.attention, stage=self.stage, experience=None, warning=None,
            reason="menu-use", feeling=feeling,
        )

    def note_motion_finished(self, token: int, now: float) -> None:
        if self.current.token != token or not self.current.moving:
            return
        self.recover_until = max(
            self.recover_until,
            now
            + (
                parameter("play_pause_seconds")
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

    def _clear_attention(self, *, clear_score: bool = True) -> None:
        if clear_score:
            self.attention, self.stage = 0.0, 0
        self._release = [0.0, 0.0, 0.0]
        self._last_sample = -100.0
        self._positive_since = None
        self._last_play_at = -100.0
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

    def _orient_body(
        self, p: CursorPerception, dt: float, feeling: CursorFeeling | None,
    ) -> None:
        if dt == 0 or self.stage == 0 or self._access:
            self._side_samples.clear()
            self._body_side = 0
            self._opposite_seconds = self._far_seconds = 0.0
            return
        far = p.distance > parameter("interest_distance")
        if feeling is not None and not far:
            self._body_side = 0
            self._side_samples.clear()
            self._opposite_seconds = self._far_seconds = 0.0
            return
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
        self._evidence_serial += 1
        return CursorExperience(
            f"{self._session}:{self._serial}:{feeling}:{level}:{self._evidence_serial}",
            feeling, level,
        )

    def _curiosity(
        self, p: CursorPerception, context: CursorBehaviourContext,
        now: float, dt: float, threat: bool,
    ) -> tuple[CursorExperience | None, bool]:
        active = context.cursor_feeling == "curiosity" or self._curiosity_level > 0
        moving = p.motion_band in ("normal", "fast", "very_fast")
        safe = (dt > 0 and moving and not threat and not self._access
                and p.distance <= parameter("interest_distance")
                and (not self._retreated or now >= self.recover_until))
        if safe and self.attention >= parameter("strong_at"):
            if self._positive_since is None:
                self._positive_since = p.sampled_at
        else:
            self._positive_since = None
        qualified = (self._positive_since is not None and p.sampled_at
                     - self._positive_since + 1e-9
                     >= parameter("positive_observation_seconds"))
        if not active and qualified:
            self._curiosity_level = 1
            self._play_seconds = 0.0
            self._last_play_at = p.sampled_at
            self._last_curiosity_evidence = now
            return self._evidence("curiosity", 1), True
        if active and safe and self.stage > 0:
            self._last_play_at = p.sampled_at
            self._play_seconds = min(
                parameter("curiosity_level_three_seconds"),
                self._play_seconds + dt * self._play_rate,
            )
            level = max(self._curiosity_level, context.cursor_level, 1)
            if self._play_seconds >= parameter("curiosity_level_three_seconds"):
                level = 3
            elif self._play_seconds >= parameter("curiosity_level_two_seconds"):
                level = max(2, level)
            if (level > self._curiosity_level or now - self._last_curiosity_evidence
                    >= parameter("curiosity_refresh_seconds")):
                self._curiosity_level = level
                self._last_curiosity_evidence = now
                return self._evidence("curiosity", level), True
        elif dt > 0:
            self._play_seconds = max(0, self._play_seconds - dt)
        engaged = active and self.stage > 0 and (safe or now - self._last_play_at
                                               <= parameter("play_grace_seconds"))
        return None, engaged

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
            self.current = CursorIntent(
                reason="invalid-sample", attention=self.attention, stage=self.stage,
            )
            return self.current
        dt = p.sampled_at - self._last_sample
        if dt <= 0:
            return self.current
        if context.cursor_feeling != self._known_feeling:
            self._known_feeling = context.cursor_feeling
            self._positive_since = None
            if context.cursor_feeling != "curiosity":
                self._curiosity_level = 0
                self._play_seconds = 0.0
                self._last_play_at = -100.0
            elif self._curiosity_level == 0:
                self._curiosity_level = context.cursor_level
                self._last_curiosity_evidence = now
            if context.cursor_feeling != "fear":
                self._fear_level = 0
        if (context.cursor_feeling == "curiosity" and 0 < context.cursor_level
                < self._curiosity_level):
            self._curiosity_level = context.cursor_level
        continuous = 0 < dt <= 1.5
        self._last_sample = p.sampled_at
        if not continuous:
            self._outside_since = None
            self.note_motion_finished(self.current.token, now)
        self._integrate(p, dt if continuous else 0.0)
        self._orient_body(p, dt if continuous else 0.0, context.cursor_feeling)
        if p.distance > parameter("interest_distance"):
            self._play_seconds = max(0, self._play_seconds - (dt if continuous else 0))
            self.note_motion_finished(self.current.token, now)
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
                feeling=context.cursor_feeling,
            )
            return self.current
        self._outside_since = None
        if not self._encounter:
            self._encounter = True
            self._serial += 1
            self._curiosity_level = (context.cursor_level
                                     if context.cursor_feeling == "curiosity" else 0)
            self._fear_level = 0
            self._trust = max(0, min(1, (context.friendship_level - 1) / 9))
            self._willing = context.energy >= 25 and context.mood >= 30
            self._play_rate = (.75 + .5 * self._trust) * (
                max(.5, min(1, context.energy / 60))
                * max(.5, min(1, context.mood / 60))
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
        if threat:
            self._threat_active = True
        elif (p.closing_speed <= 0 or p.distance > parameter("warning_distance")
              or p.motion_band == "still"):
            self._threat_active = False
        warning = None
        if (new_approach and not self._access
                and (not self._retreated or context.cursor_feeling == "curiosity")
                and (now >= self.recover_until
                     or context.cursor_feeling == "curiosity")):
            warned = self._warned_at
            if (warned is not None and warned < p.sampled_at
                    <= warned + parameter("warning_window_seconds")):
                can_retreat = not self._retreated
                if can_retreat:
                    self._motion_serial += 1
                self._retreated = True
                level = min(3, max(1, round(
                    3 - 2 * self._trust + (context.energy < 25)
                )))
                self._fear_level = level
                reaction: CursorReaction = (
                    "flee"
                    if can_retreat and self._trust < 0.45 and context.energy >= 25
                    else "avoid"
                    if can_retreat and context.energy >= 12
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
                    attention=self.attention, stage=self.stage,
                    feeling="fear",
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
        if self.current.moving and self.current.reaction != "approach":
            lost_target = p.side != 0 and self.current.side != -p.side
            if now < self.current.until and not lost_target:
                self.current = replace(
                    self.current, target=p.pointer,
                    attention=self.attention, stage=self.stage,
                    feeling=context.cursor_feeling,
                )
                return self.current
            self.note_motion_finished(self.current.token, now)
        if self.current.reaction == "startle" and now < self._look_until:
            self.current = replace(
                self.current, target=p.pointer, side=self._body_side,
                body="three_quarter" if self._body_side else "front",
                attention=self.attention, stage=self.stage,
                feeling=context.cursor_feeling,
            )
            return self.current
        experience, engaged = self._curiosity(
            p, context, now, dt if continuous else 0.0, threat,
        )
        if self.current.reaction == "approach":
            if (now < self.current.until and engaged and not threat
                    and now - self._last_play_at <= parameter("play_grace_seconds")):
                self.current = replace(
                    self.current, side=p.side, target=p.pointer,
                    body="profile" if p.side else "front",
                    attention=self.attention, stage=self.stage,
                    experience=experience, feeling="curiosity",
                )
                return self.current
            self.note_motion_finished(self.current.token, now)
        body: BodyIntent = "three_quarter" if self._body_side else "front"
        reaction = "observe" if self.stage else "ignore"
        until = now + 2 if engaged else self._look_until
        if (
            not self._access and self._willing and not threat
            and now >= self.recover_until and engaged
            and self._last_play_at == p.sampled_at and p.side != 0
        ):
            self._motion_serial += 1
            reaction, body = "approach", "profile"
            until = now + parameter("play_attempt_seconds")
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
            2 * self._curiosity_level + 1,
            self.attention,
            self.stage,
            warning,
            experience.feeling if experience is not None else context.cursor_feeling,
            self._curiosity_level >= 2,
        )
        return self.current
