"""Authored German dialogue catalogue, strict schema and weighted rotation.

This module owns the available lines; it does not decide when Aiko should
speak. PetMind in mind.py owns situational behavior and conversation.
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from typing import Any, Literal

from ..balance import BALANCE
from ..catalog_validation import load_json, object_fields
from ..object_text_contract import OBJECT_TEXT_FIELDS
from ..routine import TimeContext
from .dialogue_context import DialogueContext, FriendshipStage
from .dialogue_events import DIALOGUE_EVENTS
from .reaction_sequence import Cue

CATALOGUE = Path(__file__).resolve().parents[2] / "data" / "dialogues.de.json"
ANIMATIONS = frozenset({
    "idle",
    "waiting",
    "review",
    "failed",
    "waving",
    "waving-greeting",
    "jumping",
    "eat",
    "petting",
})
EMOTIONS = frozenset({
    "asleep",
    "irritated",
    "tired",
    "hungry",
    "withdrawn",
    "warm",
    "playful",
    "calm",
    "lonely",
    "seeking_affection",
})
PERIODS = frozenset({
    "night",
    "breakfast",
    "quiet",
    "lunch",
    "free",
    "dinner",
    "evening",
})


@dataclass(frozen=True)
class Line:
    id: str
    event: str
    beats: tuple[Cue, ...]
    animation: str
    moods: tuple[str, ...]
    periods: tuple[str, ...]
    weekdays: tuple[int, ...]
    weight: int = BALANCE.integer("dialogue", "default_weight")
    cooldown_seconds: float = BALANCE.integer("dialogue", "default_cooldown_seconds")
    stages: tuple[FriendshipStage, ...] = ()
    needs: frozenset[str] = frozenset()
    presentation: Literal["short", "story"] = "short"
    requires_present: bool = False

    @property
    def text(self) -> str:
        return next(beat.content for beat in self.beats if beat.kind == "text")

    @classmethod
    def parse(cls, raw: Any) -> Line:
        data = object_fields(
            raw,
            ("id", "event", "beats", "animation", "moods", "periods", "weekdays"),
            optional=(
                "weight",
                "cooldown_seconds",
                "stages",
                "needs",
                "presentation",
                "requires_present",
            ),
            context="dialogue line",
        )
        for key in ("id", "event", "animation"):
            if not isinstance(data[key], str) or not data[key].strip():
                raise ValueError(f"Invalid dialogue {key}")
        if data["event"] not in DIALOGUE_EVENTS or data["animation"] not in ANIMATIONS:
            raise ValueError("Unknown dialogue event or animation")
        for key, allowed in (
            ("moods", EMOTIONS),
            ("periods", PERIODS),
            ("stages", frozenset(FriendshipStage)),
            ("needs", EMOTIONS),
        ):
            values = data.get(key, [])
            if not isinstance(values, list) or any(
                not isinstance(value, str) or value not in allowed for value in values
            ):
                raise ValueError(f"Invalid dialogue {key}")
        days = data["weekdays"]
        if not isinstance(days, list) or any(
            type(day) is not int or not 0 <= day <= 6 for day in days
        ):
            raise ValueError("Invalid weekdays")
        raw_beats = data["beats"]
        if not isinstance(raw_beats, list) or not 1 <= len(raw_beats) <= 16:
            raise ValueError("Invalid dialogue beats")
        beats = tuple(Cue.parse(beat) for beat in raw_beats)
        texts = [beat.content for beat in beats if beat.kind == "text"]
        presentation = data.get("presentation", "short")
        if presentation not in ("short", "story"):
            raise ValueError("Invalid presentation")
        if not 1 <= len(texts) <= (5 if presentation == "story" else 2):
            raise ValueError("Invalid number of speech bubbles")
        for phrase in texts:
            try:
                fields = list(Formatter().parse(phrase))
            except ValueError as error:
                raise ValueError("Invalid dialogue template") from error
            for _, field, spec, conversion in fields:
                if field is not None and (
                    not data["event"].startswith("object_")
                    or field not in OBJECT_TEXT_FIELDS
                    or spec
                    or conversion
                ):
                    raise ValueError("Invalid dialogue placeholder")
        weight = data.get("weight", BALANCE.integer("dialogue", "default_weight"))
        cooldown = data.get(
            "cooldown_seconds", BALANCE.integer("dialogue", "default_cooldown_seconds")
        )
        if type(weight) is not int or not 1 <= weight <= 10:
            raise ValueError("Invalid dialogue weight")
        if (
            type(cooldown) not in (int, float)
            or not math.isfinite(cooldown)
            or not 0 <= cooldown <= 86400
        ):
            raise ValueError("Invalid dialogue cooldown")
        present = data.get("requires_present", False)
        if type(present) is not bool:
            raise ValueError("Invalid presence filter")
        return cls(
            data["id"],
            data["event"],
            beats,
            data["animation"],
            tuple(data["moods"]),
            tuple(data["periods"]),
            tuple(days),
            weight,
            float(cooldown),
            tuple(FriendshipStage(s) for s in data.get("stages", [])),
            frozenset(data.get("needs", [])),
            presentation,
            present,
        )

    def matches(
        self,
        emotion: str,
        context: TimeContext,
        dialogue: DialogueContext | None = None,
    ) -> bool:
        return (
            (not self.moods or emotion in self.moods)
            and (not self.periods or context.period in self.periods)
            and (not self.weekdays or context.local.weekday() in self.weekdays)
            and (
                not self.stages
                or dialogue is not None
                and dialogue.stage in self.stages
            )
            and (
                not self.needs or dialogue is not None and self.needs <= dialogue.states
            )
            and (
                not self.requires_present
                or dialogue is not None
                and dialogue.present is True
            )
        )

    def specificity(self) -> int:
        return bool(self.moods) + bool(self.stages) + len(self.needs)

    def selection_weight(self) -> int:
        return self.weight * (
            1 + 2 * bool(self.moods) + 2 * bool(self.periods) + 2 * bool(self.weekdays)
        )


@dataclass(frozen=True)
class Reaction:
    """An already selected, immutable sequence; playback never reselects text."""

    line_id: str
    beats: tuple[Cue, ...]
    animation: str
    event: str
    presentation: Literal["short", "story"] = "short"

    @property
    def text(self) -> str:
        return next(beat.content for beat in self.beats if beat.kind == "text")

    @classmethod
    def spoken(cls, line_id: str, text: str, animation: str, event: str) -> Reaction:
        return cls(line_id, (Cue.text(text),), animation, event)


class DialogueBook:
    """Context-filtered rotation; no fallback can cross a relationship boundary."""

    def __init__(self, lines: tuple[Line, ...], *, rng: random.Random | None = None):
        if not lines or len({line.id for line in lines}) != len(lines):
            raise ValueError("Empty dialogue book or duplicate dialogue IDs")
        self.lines = lines
        self.rng = rng or random.Random()
        self.last_used: dict[str, float] = {}
        self.recent: deque[str] = deque(
            maxlen=BALANCE.integer("dialogue", "recent_line_history")
        )
        self._story_used: set[str] = set()

    @classmethod
    def from_file(
        cls, file: Path = CATALOGUE, *, rng: random.Random | None = None
    ) -> DialogueBook:
        data = object_fields(
            load_json(file),
            ("catalogue_version", "language", "lines"),
            context="dialogues",
        )
        if (
            type(data["catalogue_version"]) is not int
            or data["catalogue_version"] != 2
            or data["language"] != "de"
        ):
            raise ValueError("Unsupported dialogue catalogue version")
        if not isinstance(data["lines"], list):
            raise ValueError("Missing dialogue lines")
        return cls(tuple(Line.parse(item) for item in data["lines"]), rng=rng)

    def choose(
        self,
        event: str,
        emotion: str,
        context: TimeContext,
        now: float,
        *,
        dialogue: DialogueContext | None = None,
        presentation: Literal["short", "story"] | None = None,
    ) -> Reaction | None:
        candidates = [
            line
            for line in self.lines
            if line.event == event
            and line.matches(emotion, context, dialogue)
            and (presentation is None or line.presentation == presentation)
        ]
        if not candidates:
            return None
        specificity = max(line.specificity() for line in candidates)
        candidates = [line for line in candidates if line.specificity() == specificity]
        if candidates[0].presentation == "story":
            unseen = [line for line in candidates if line.id not in self._story_used]
            if not unseen:
                self._story_used.difference_update(line.id for line in candidates)
                unseen = candidates
            candidates = unseen
        fresh = [
            line
            for line in candidates
            if line.id not in self.recent
            and now - self.last_used.get(line.id, float("-inf"))
            >= line.cooldown_seconds
        ]
        if not fresh:
            fresh = [line for line in candidates if line.id not in self.recent]
        if not fresh:
            fresh = [
                line
                for line in candidates
                if not self.recent or line.id != self.recent[-1]
            ]
        if not fresh:
            fresh = candidates
        line = self.rng.choices(
            fresh, weights=[x.selection_weight() for x in fresh], k=1
        )[0]
        self.last_used[line.id] = now
        self.recent.append(line.id)
        if line.presentation == "story":
            self._story_used.add(line.id)
        return Reaction(line.id, line.beats, line.animation, event, line.presentation)
