"""Authored German dialogue catalogue, strict schema and weighted rotation.

This module owns the available lines; it does not decide when Aiko should
speak. AikoMind in mind.py owns situational behavior and conversation.
"""

from __future__ import annotations

import json
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .reaction_sequence import EMOTES as EMOTES
from ..routine import TimeContext as TimeContext

CATALOGUE = (
    Path(__file__).resolve().parents[2] / "data" / "dialogues.de.json"
)
ANIMATIONS = frozenset({
    "idle", "waiting", "review", "failed", "waving", "waving-greeting",
    "jumping", "eat", "petting",
})
EMOTIONS = frozenset({
    "asleep", "irritated", "tired", "hungry", "withdrawn", "warm", "playful", "calm",
    "lonely", "seeking_affection",
})
PERIODS = frozenset({
    "night", "breakfast", "quiet", "lunch", "free", "dinner", "evening",
})

EMOTION_LABELS = {
    "asleep": "Schläfrig",
    "irritated": "Gereizt",
    "tired": "Müde",
    "hungry": "Hungrig",
    "withdrawn": "Nachdenklich",
    "warm": "Zugewandt",
    "playful": "Verspielt",
    "calm": "Gelassen",
    "lonely": "Vermisst Gesellschaft",
    "seeking_affection": "Wünscht Zuwendung",
}


@dataclass(frozen=True)
class Line:
    id: str
    event: str
    text: str
    animation: str
    moods: tuple[str, ...]
    periods: tuple[str, ...]
    weekdays: tuple[int, ...]
    weight: int
    cooldown_seconds: float
    followup_text: str | None = None
    followup_delay_ms: int = 1400
    emote_before: str | None = None
    emote_after: str | None = None

    @classmethod
    def parse(cls, raw: Any) -> Line:
        if not isinstance(raw, dict):
            raise ValueError("A dialogue line must be an object")
        required = ("id", "event", "text", "animation", "moods", "periods", "weekdays")
        if any(key not in raw for key in required):
            raise ValueError("Incomplete dialogue line")
        for key in ("id", "event", "text", "animation"):
            if not isinstance(raw[key], str) or not raw[key].strip():
                raise ValueError(f"Invalid dialogue {key}")
        if not 1 <= len(raw["text"]) <= 125:
            raise ValueError("Dialogue line is too long")
        if raw["animation"] not in ANIMATIONS:
            raise ValueError("No matching physical sprite animation")
        for key in ("moods", "periods", "weekdays"):
            if not isinstance(raw[key], list):
                raise ValueError(f"Invalid dialogue {key}")
        moods, periods, weekdays = raw["moods"], raw["periods"], raw["weekdays"]
        if any(m not in EMOTIONS for m in moods):
            raise ValueError("Unknown emotion")
        if any(p not in PERIODS for p in periods):
            raise ValueError("Unknown day period")
        if any(type(day) is not int or not 0 <= day <= 6 for day in weekdays):
            raise ValueError("Invalid weekday")
        weight = raw.get("weight", 1)
        cooldown = raw.get("cooldown_seconds", 120)
        if type(weight) is not int or not 1 <= weight <= 10:
            raise ValueError("Invalid line weight")
        if type(cooldown) not in (int, float) or not 0 <= cooldown <= 86400:
            raise ValueError("Invalid cooldown")
        followup = raw.get("followup_text")
        delay = raw.get("followup_delay_ms", 1400)
        if followup is not None and (
            not isinstance(followup, str) or not 1 <= len(followup) <= 125
        ):
            raise ValueError("Invalid follow-up text")
        if type(delay) is not int or not 600 <= delay <= 2600:
            raise ValueError("Invalid follow-up timing")
        before = raw.get("emote_before")
        after = raw.get("emote_after")
        if any(emote is not None and (
            not isinstance(emote, str) or emote not in EMOTES
        ) for emote in (before, after)):
            raise ValueError("Unknown or unavailable emote")
        return cls(
            id=raw["id"], event=raw["event"], text=raw["text"],
            animation=raw["animation"], moods=tuple(moods),
            periods=tuple(periods), weekdays=tuple(weekdays),
            weight=weight, cooldown_seconds=float(cooldown),
            followup_text=followup, followup_delay_ms=delay,
            emote_before=before, emote_after=after,
        )

    def matches(self, emotion: str, context: TimeContext) -> bool:
        return (
            (not self.moods or emotion in self.moods)
            and (not self.periods or context.period in self.periods)
            and (not self.weekdays or context.local.weekday() in self.weekdays)
        )

    def score(self, emotion: str, context: TimeContext) -> int:
        """Relevant, specific entries win more often than generic fallbacks."""
        return self.weight * (
            1 + 2 * bool(self.moods and emotion in self.moods)
            + 2 * bool(self.periods and context.period in self.periods)
            + 2 * bool(self.weekdays and context.local.weekday() in self.weekdays)
        )


@dataclass(frozen=True)
class Reaction:
    """An actual available animation plus a short German speech bubble."""

    line_id: str
    text: str
    animation: str
    event: str
    followup_text: str | None = None
    followup_delay_ms: int = 1400
    emote_before: str | None = None
    emote_after: str | None = None


class DialogueBook:
    """Filtered weighted rotation with no immediate repeats or rapid spam."""

    def __init__(self, lines: tuple[Line, ...], *, rng: random.Random | None = None):
        if len({line.id for line in lines}) != len(lines):
            raise ValueError("Duplicate dialogue IDs")
        if not lines:
            raise ValueError("Empty dialogue book")
        self.lines = lines
        self.rng = rng or random.Random()
        self.last_used: dict[str, float] = {}
        self.recent: deque[str] = deque(maxlen=6)

    @classmethod
    def from_file(
        cls, file: Path = CATALOGUE, *, rng: random.Random | None = None,
    ) -> DialogueBook:
        data = json.loads(file.read_text(encoding="utf-8"))
        if data.get("catalogue_version") != 1 or data.get("language") != "de":
            raise ValueError("Unsupported dialogue catalogue version")
        if not isinstance(data.get("lines"), list):
            raise ValueError("Dialogue book has no lines")
        return cls(tuple(Line.parse(item) for item in data["lines"]), rng=rng)

    def choose(
        self, event: str, emotion: str, context: TimeContext, now: float,
    ) -> Reaction | None:
        candidates = [
            line for line in self.lines
            if line.event == event and line.matches(emotion, context)
        ]
        if not candidates:
            return None
        fresh = [
            line for line in candidates
            if line.id not in self.recent
            and (
                now - self.last_used.get(line.id, float("-inf"))
                >= line.cooldown_seconds
            )
        ]
        if not fresh:
            fresh = [line for line in candidates if line.id not in self.recent]
        if not fresh:
            last_used_id = self.recent[-1] if self.recent else ""
            fresh = [line for line in candidates if line.id != last_used_id]
        if not fresh:
            fresh = candidates
        weights = [line.score(emotion, context) for line in fresh]
        line = self.rng.choices(fresh, weights=weights, k=1)[0]
        self.last_used[line.id] = now
        self.recent.append(line.id)
        return Reaction(
            line.id, line.text, line.animation, event,
            line.followup_text, line.followup_delay_ms,
            line.emote_before, line.emote_after,
        )
