"""Authored German dialogue catalogue, strict schema and weighted rotation.

This module owns the available lines; it does not decide when Aiko should
speak. PetMind in mind.py owns situational behavior and conversation.
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from string import Formatter
from typing import Any, Literal

from ...games.contracts import BlackjackDetails, GameId, RockPaperScissorsDetails
from ..balance import BALANCE
from ..catalog_validation import enum_value, load_json, object_fields
from ..content import GERMAN_TEXT
from ..emotions import EmotionalState
from ..food_catalog import DEFAULT_CATALOG
from ..interaction_events import SocialCompletion
from ..moodlets import (
    EmotionalDirection,
    MoodletAttribution,
    MoodletCauseKind,
    MoodletOutcome,
)
from ..needs import NeedCondition
from ..object_text_contract import OBJECT_TEXT_FIELDS
from ..text_contract import TEXT_FIELDS
from ..wish_catalog import WISH_CATALOG
from ..wishes import ActiveWish, WishArea, WishId, WishObjective, wish_text_key
from .conversation_topics import (
    CONVERSATION_KEYS,
    CONVERSATION_TEXT_FIELDS,
    conversation_fields,
)
from .dialogue_context import (
    DialogueConditions,
    DialogueContext,
    FriendshipStage,
    ReactionTone,
    SituationalCondition,
)
from .dialogue_events import DIALOGUE_EVENTS
from .reaction_sequence import Cue, conversation_timing

CATALOGUE = (
    Path(__file__).resolve().parents[2] / "data" / "dialogues" / "de" / "index.json"
)
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
PERIODS = frozenset({
    "night",
    "breakfast",
    "quiet",
    "lunch",
    "free",
    "dinner",
    "evening",
})


def render_wish_text(wish: ActiveWish) -> str:
    """Use the same existing authored wish utterance for both speech contexts."""
    definition = WISH_CATALOG.definitions[wish.definition_id]
    key = wish_text_key(wish.definition_id, wish.goal_snapshot, "utterance",
                        target_id=wish.target_id)
    values: dict[str, str] = {}
    if definition.area == WishArea.FOOD:
        values["target"] = DEFAULT_CATALOG.foods[wish.target_id].display_name
    elif definition.area == WishArea.GAMES:
        values["target"] = GERMAN_TEXT.format(f"game.name.{wish.target_id}")
        if "rounds" in TEXT_FIELDS[key]:
            values["rounds"] = str(wish.goal_snapshot.required_count)
    return GERMAN_TEXT.format(key, **values)


def _parse_conditions(raw: Any) -> tuple[DialogueConditions, ...]:
    if not isinstance(raw, list) or len(raw) > 8:
        raise ValueError("Invalid dialogue condition alternatives")
    result = []
    for value in raw:
        row = object_fields(
            value,
            (),
            optional=(
                "emotional_states",
                "emotional_directions",
                "need_conditions",
                "reaction_tones",
                "situational_conditions",
                "sleeping",
                "conversation_topics",
                "conversation_attributions",
                "conversation_causes",
                "conversation_objectives",
                "conversation_targets",
                "conversation_outcomes",
                "conversation_round_outcomes",
                "conversation_wishes",
            ),
            context="dialogue conditions",
        )
        if not row or "sleeping" in row and type(row["sleeping"]) is not bool:
            raise ValueError("Empty or invalid dialogue conditions")
        for key in (
            "emotional_states",
            "emotional_directions",
            "need_conditions",
            "reaction_tones",
            "situational_conditions",
            "conversation_topics",
            "conversation_attributions",
            "conversation_causes",
            "conversation_objectives",
            "conversation_targets",
            "conversation_outcomes",
            "conversation_round_outcomes",
            "conversation_wishes",
        ):
            items = row.get(key, [])
            if not isinstance(items, list) or not all(
                isinstance(i, str) for i in items
            ):
                raise ValueError("Invalid typed dialogue condition")
        result.append(
            DialogueConditions(
                frozenset(
                    enum_value(v, EmotionalState, context="emotional state")
                    for v in row.get("emotional_states", [])
                ),
                frozenset(
                    enum_value(v, EmotionalDirection, context="emotional direction")
                    for v in row.get("emotional_directions", [])
                ),
                frozenset(
                    enum_value(v, NeedCondition, context="need condition")
                    for v in row.get("need_conditions", [])
                ),
                frozenset(
                    enum_value(v, ReactionTone, context="reaction tone")
                    for v in row.get("reaction_tones", [])
                ),
                frozenset(
                    enum_value(v, SituationalCondition, context="situation")
                    for v in row.get("situational_conditions", [])
                ),
                row.get("sleeping"),
                frozenset(row.get("conversation_topics", [])),
                frozenset(enum_value(v, MoodletAttribution, context="cause attribution")
                          for v in row.get("conversation_attributions", [])),
                frozenset(enum_value(v, MoodletCauseKind, context="conversation cause")
                          for v in row.get("conversation_causes", [])),
                frozenset(enum_value(v, WishObjective, context="conversation objective")
                          for v in row.get("conversation_objectives", [])),
                frozenset(row.get("conversation_targets", [])),
                frozenset(enum_value(v, MoodletOutcome, context="conversation outcome")
                          for v in row.get("conversation_outcomes", [])),
                frozenset(enum_value(v, MoodletOutcome, context="conversation round")
                          for v in row.get("conversation_round_outcomes", [])),
                frozenset(enum_value(v, WishId, context="conversation source wish")
                          for v in row.get("conversation_wishes", [])),
            )
        )
        if not result[-1].conversation_topics <= CONVERSATION_KEYS:
            raise ValueError("Unknown conversation topic")
        if not result[-1].conversation_targets <= (
            set(DEFAULT_CATALOG.foods) | {game.value for game in GameId}
            | {"chat", "single", "twopart", "fact", "pet"}
        ):
            raise ValueError("Unknown conversation target")
    return tuple(result)


@dataclass(frozen=True)
class Line:
    id: str
    event: str
    beats: tuple[Cue, ...]
    animation: str
    conditions: tuple[DialogueConditions, ...]
    periods: tuple[str, ...]
    weekdays: tuple[int, ...]
    weight: int = BALANCE.integer("dialogue", "default_weight")
    cooldown_seconds: float = BALANCE.integer("dialogue", "default_cooldown_seconds")
    stages: tuple[FriendshipStage, ...] = ()
    presentation: Literal["short", "story"] = "short"
    requires_present: bool = False

    @property
    def text(self) -> str:
        return next(beat.content for beat in self.beats if beat.kind == "text")

    @classmethod
    def parse(cls, raw: Any) -> Line:
        data = object_fields(
            raw,
            ("id", "event", "beats", "animation", "periods", "weekdays"),
            optional=(
                "weight",
                "cooldown_seconds",
                "stages",
                "conditions",
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
            ("periods", PERIODS),
            ("stages", frozenset(FriendshipStage)),
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
                    field not in (OBJECT_TEXT_FIELDS
                                  if data["event"].startswith("object_") else
                                  CONVERSATION_TEXT_FIELDS if data["event"] == "talk"
                                  else frozenset())
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
        conditions = _parse_conditions(data.get("conditions", []))
        if data["event"] == "talk" and (
            not conditions or any(not c.conversation_topics for c in conditions)
        ):
            raise ValueError("Requested chat requires a grounded conversation topic")
        if data["event"] == "talk":
            required = {field for text in texts
                        for _, field, _, _ in Formatter().parse(text) if field}
            if any(not required <= conversation_fields(topic)
                   for condition in conditions
                   for topic in condition.conversation_topics):
                raise ValueError("Conversation placeholder is not proved by its topic")
        return cls(
            data["id"],
            data["event"],
            beats,
            data["animation"],
            conditions,
            tuple(data["periods"]),
            tuple(days),
            weight,
            float(cooldown),
            tuple(FriendshipStage(s) for s in data.get("stages", [])),
            presentation,
            present,
        )

    def matches(self, context: DialogueContext) -> bool:
        return (
            (not self.conditions or any(c.matches(context) for c in self.conditions))
            and (not self.periods or context.time.period in self.periods)
            and (not self.weekdays or context.time.local.weekday() in self.weekdays)
            and (not self.stages or context.stage in self.stages)
            and (not self.requires_present or context.present is True)
        )

    def specificity(self, context: DialogueContext) -> tuple[int, int]:
        rank = max(
            (c.specificity() for c in self.conditions if c.matches(context)),
            default=(0, 0),
        )
        return bool(self.stages) + rank[0], rank[1]

    def selection_weight(self) -> int:
        return self.weight * (
            1
            + 2 * bool(self.conditions)
            + 2 * bool(self.periods)
            + 2 * bool(self.weekdays)
        )


@dataclass(frozen=True)
class Reaction:
    """An already selected, immutable sequence; playback never reselects text."""

    line_id: str
    beats: tuple[Cue, ...]
    animation: str
    event: str
    presentation: Literal["short", "story"] = "short"
    completed_social: SocialCompletion | None = None
    wish_instance_id: int | None = None

    def __post_init__(self) -> None:
        if self.event == "talk":
            object.__setattr__(self, "beats", conversation_timing(self.beats))

    @property
    def text(self) -> str:
        return next(beat.content for beat in self.beats if beat.kind == "text")

    @classmethod
    def spoken(cls, line_id: str, text: str, animation: str, event: str) -> Reaction:
        return cls(line_id, (Cue.text(text),), animation, event)


def _source_lines(raw: Any) -> tuple[Line, ...]:
    data = object_fields(
        raw, ("catalogue_version", "language", "lines"), context="dialogues",
    )
    if (
        type(data["catalogue_version"]) is not int
        or data["catalogue_version"] != 3
        or data["language"] != "de"
    ):
        raise ValueError("Unsupported dialogue catalogue version")
    if not isinstance(data["lines"], list):
        raise ValueError("Missing dialogue lines")
    return tuple(Line.parse(item) for item in data["lines"])


def _indexed_lines(file: Path, raw: Any) -> tuple[Line, ...]:
    data = object_fields(
        raw,
        ("index_version", "catalogue_version", "language", "files", "line_order"),
        context="dialogue index",
    )
    if (
        type(data["index_version"]) is not int or data["index_version"] != 1
        or type(data["catalogue_version"]) is not int
        or data["catalogue_version"] != 3 or data["language"] != "de"
    ):
        raise ValueError("Unsupported dialogue index version or language")
    names = data["files"]
    if (not isinstance(names, list) or not names
            or any(not isinstance(name, str) or not name for name in names)):
        raise ValueError("Invalid dialogue source files")
    if len(set(names)) != len(names):
        raise ValueError("Duplicate dialogue source file")
    root = file.parent.resolve()
    lines: list[Line] = []
    for name in names:
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts
                or "\\" in name or ":" in name
                or relative.as_posix() != name or relative.suffix != ".json"):
            raise ValueError(f"Invalid dialogue source path: {name}")
        source = (root / name).resolve()
        if not source.is_relative_to(root) or source == file.resolve():
            raise ValueError(f"Dialogue source outside index or recursive: {name}")
        lines.extend(_source_lines(load_json(source)))
    by_id = {line.id: line for line in lines}
    if len(by_id) != len(lines):
        raise ValueError("Duplicate dialogue IDs across source files")
    order = data["line_order"]
    if (not isinstance(order, list)
            or any(not isinstance(item, str) or not item for item in order)):
        raise ValueError("Invalid dialogue line order")
    if len(order) != len(set(order)) or set(order) != set(by_id):
        raise ValueError("Dialogue line order must name every source ID exactly once")
    return tuple(by_id[item] for item in order)


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
        """Read one indexed book or an explicitly supplied single-source catalogue."""
        data = load_json(file)
        lines = (
            _indexed_lines(file, data)
            if isinstance(data, dict) and "index_version" in data
            else _source_lines(data)
        )
        return cls(lines, rng=rng)

    def choose(
        self,
        event: str,
        context: DialogueContext,
        now: float,
        *,
        presentation: Literal["short", "story"] | None = None,
    ) -> Reaction | None:
        candidates = [
            line
            for line in self.lines
            if line.event == event
            and line.matches(context)
            and (presentation is None or line.presentation == presentation)
        ]
        if not candidates:
            return None
        specificity = max(line.specificity(context) for line in candidates)
        candidates = [
            line for line in candidates if line.specificity(context) == specificity
        ]
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
        beats = line.beats
        if event == "talk" and context.conversation_topic is not None:
            topic = context.conversation_topic
            cause = topic.cause
            values: dict[str, str] = {}
            if topic.wish is not None:
                values["wish_text"] = render_wish_text(topic.wish)
            if cause is not None:
                target = cause.target_id
                if target in DEFAULT_CATALOG.foods:
                    assert target is not None
                    values["target"] = DEFAULT_CATALOG.foods[target].display_name
                elif target in {game.value for game in GameId}:
                    values["target"] = GERMAN_TEXT.format(f"game.name.{target}")
                if cause.wish is not None:
                    values["count"] = str(cause.wish.required_count)
                if isinstance(cause.game_details, BlackjackDetails):
                    values["player_total"] = str(cause.game_details.player_total)
                    values["aiko_total"] = str(cause.game_details.aiko_total)
                if isinstance(cause.game_details, RockPaperScissorsDetails):
                    values["aiko_move"] = GERMAN_TEXT.format(
                        f"rps.move.{cause.game_details.aiko_move.value}",
                    )
                    values["player_move"] = GERMAN_TEXT.format(
                        f"rps.move.{cause.game_details.player_move.value}",
                    )
            beats = tuple(Cue.text(beat.content.format(**values))
                          if beat.kind == "text" else beat for beat in beats)
        return Reaction(line.id, beats, line.animation, event, line.presentation)
