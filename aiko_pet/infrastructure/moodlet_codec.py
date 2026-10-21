"""Versioned Moodlet storage on the existing pet elapsed axis; no ageing."""

from __future__ import annotations

from typing import Any

from ..pet.balance import BALANCE
from ..pet.catalog_validation import (
    enum_value,
    integer_value,
    number_value,
    object_fields,
)
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.interaction_events import FoodRepetitionMemory, InteractionMemory
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlets import (
    MAX_MOODLET_CAUSES,
    FoodMonotonyParameters,
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletDecay,
    MoodletEpisode,
    MoodletGameResult,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
    PettingParameters,
    PokingParameters,
)
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import WishArea, WishId
from .poor_care_codec import decode_poor_care, encode_poor_care
from .wish_codec import decode_wish_goal


def _token(raw: Any) -> str:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise ValueError("Invalid Moodlet cause identity")
    return raw


def _wish_cause(raw: Any) -> MoodletWishCause:
    row = object_fields(raw, ("instance_id", "definition_id", "target_id",
                              "objective", "required_count"),
                        context="Moodlet source wish")
    key = enum_value(row["definition_id"], WishId, context="Moodlet source wish")
    goal = decode_wish_goal(dict(objective=row["objective"],
                                 required_count=row["required_count"]), key)
    target = _token(row["target_id"])
    if target not in WISH_CATALOG.definitions[key].targets:
        raise ValueError("Incompatible Moodlet source wish target")
    return MoodletWishCause(
        integer_value(row["instance_id"], minimum=1, maximum=2**63 - 2,
                      context="Moodlet source wish instance"),
        key.value, target, goal.objective.value, goal.required_count,
    )


def _decode_causes(
    raw: Any, *, started: float, trigger: float, key: MoodletId,
) -> tuple[MoodletCause, ...]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_MOODLET_CAUSES:
        raise ValueError("Moodlet needs one to three bounded causes")
    causes = []
    receipts: set[tuple[MoodletCauseKind, str | None, int | None]] = set()
    previous = started
    levels: set[int] = set()
    for value in raw:
        row = object_fields(value, ("kind", "occurred_at", "event_id", "attribution",
                                    "wish", "target_id", "outcome", "object_id"),
                            optional=("game", "level"), context="Moodlet cause")
        kind = enum_value(row["kind"], MoodletCauseKind, context="Moodlet cause kind")
        at = number_value(row["occurred_at"], minimum=previous, maximum=trigger,
                          context="Moodlet cause time")
        event = None if row["event_id"] is None else _token(row["event_id"])
        target = None if row["target_id"] is None else _token(row["target_id"])
        object_id = None if row["object_id"] is None else _token(row["object_id"])
        outcome = enum_value(row["outcome"], MoodletOutcome, context="Moodlet outcome")
        wish = None if row["wish"] is None else _wish_cause(row["wish"])
        game = None if row.get("game") is None else _game_result(row["game"])
        level = (None if row.get("level") is None else integer_value(
            row["level"], minimum=1,
            maximum=len(MOODLET_CATALOG.definitions[key].level_points),
            context="Moodlet cause stage",
        ))
        if level is not None:
            if level in levels or kind == MoodletCauseKind.LEGACY:
                raise ValueError("Moodlet cause stage must be real and unique")
            levels.add(level)
        if (kind == MoodletCauseKind.LEGACY and (
                len(raw) != 1 or event is not None or wish is not None
                or target is not None or object_id is not None
                or game is not None
                or outcome != MoodletOutcome.UNKNOWN)
                or kind != MoodletCauseKind.LEGACY and event is None
                or (kind in (MoodletCauseKind.WISH_FULFILLED,
                             MoodletCauseKind.WISH_FAILED)) != (wish is not None)):
            raise ValueError("Inconsistent Moodlet cause evidence")
        if wish is not None:
            definition = WISH_CATALOG.definitions[WishId(wish.definition_id)]
            if game is not None and definition.area != WishArea.GAMES:
                raise ValueError("Game result requires a game wish cause")
            if kind == MoodletCauseKind.WISH_FULFILLED:
                if (definition.fulfillment_moodlet != key
                        or outcome == MoodletOutcome.UNKNOWN):
                    raise ValueError("Incompatible Moodlet fulfillment cause")
            elif (key != MoodletId.DISAPPOINTED or outcome != MoodletOutcome.LOSS
                  or definition.id not in (WishId.AVOID_ROUND_LOSS,
                                            WishId.AVOID_OVERALL_LOSS)):
                raise ValueError("Incompatible Moodlet failure cause")
            if definition.area == WishArea.FOOD:
                if target is not None and target not in DEFAULT_CATALOG.foods:
                    raise ValueError("Unknown actual food in Moodlet cause")
            elif target is not None and target != wish.target_id:
                raise ValueError("Mismatched actual Moodlet target")
        elif game is not None:
            raise ValueError("Game result requires an original wish")
        cause = MoodletCause(
            kind, at, event,
            enum_value(row["attribution"], MoodletAttribution,
                       context="Moodlet cause attribution"),
            wish, target, outcome, object_id, game, level,
        )
        if cause.receipt in receipts:
            raise ValueError("Duplicate Moodlet cause receipt")
        receipts.add(cause.receipt)
        causes.append(cause)
        previous = at
    return tuple(causes)


def _game_result(raw: Any) -> MoodletGameResult:
    row = object_fields(raw, ("round_outcome", "completed_rounds", "wins", "losses"),
                        context="Moodlet game result")
    outcome = enum_value(row["round_outcome"], MoodletOutcome,
                         context="Moodlet settled round outcome")
    rounds = integer_value(row["completed_rounds"], minimum=1, maximum=2**63 - 1,
                           context="Moodlet completed rounds")
    wins = integer_value(row["wins"], minimum=0, maximum=rounds,
                         context="Moodlet game wins")
    losses = integer_value(row["losses"], minimum=0, maximum=rounds - wins,
                           context="Moodlet game losses")
    if (outcome not in (MoodletOutcome.WIN, MoodletOutcome.LOSS, MoodletOutcome.DRAW)
            or outcome == MoodletOutcome.WIN and wins == 0
            or outcome == MoodletOutcome.LOSS and losses == 0
            or outcome == MoodletOutcome.DRAW and rounds == wins + losses):
        raise ValueError("Inconsistent Moodlet settled game result")
    return MoodletGameResult(outcome, rounds, wins, losses)


def _encode_cause(cause: MoodletCause) -> dict[str, Any]:
    wish = cause.wish
    return dict(
        kind=cause.kind.value, occurred_at=cause.occurred_at, level=cause.level,
        event_id=cause.event_id, attribution=cause.attribution.value,
        target_id=cause.target_id, outcome=cause.outcome.value,
        object_id=cause.object_id,
        game=None if cause.game is None else dict(
            round_outcome=cause.game.round_outcome.value,
            completed_rounds=cause.game.completed_rounds,
            wins=cause.game.wins, losses=cause.game.losses,
        ),
        wish=None if wish is None else dict(
            instance_id=wish.instance_id, definition_id=wish.definition_id,
            target_id=wish.target_id, objective=wish.objective,
            required_count=wish.required_count,
        ),
    )


def decode_moodlets(raw: Any, elapsed: float) -> MoodletState:
    """Reject corrupt sections as a whole; callers retain unrelated pet values."""
    row = object_fields(raw, ("version", "baseline", "next_instance_id", "active"),
                        optional=("interactions", "poor_care"), context="moodlets")
    if type(row["version"]) is not int or row["version"] != 1:
        raise ValueError("Unsupported saved Moodlet version")
    baseline = number_value(row["baseline"], minimum=0, maximum=elapsed,
                            context="moodlets.baseline")
    next_id = integer_value(row["next_instance_id"], minimum=1,
                            maximum=2**63 - 1, context="moodlets.next_instance_id")
    rows = row["active"]
    if not isinstance(rows, list) or len(rows) > len(MoodletId):
        raise ValueError("Unbounded Moodlet family collection")
    episodes: list[MoodletEpisode] = []
    instances: set[int] = set()
    families: set[MoodletId] = set()
    for value in rows:
        entry = object_fields(value, (
            "instance_id", "definition_id", "level", "started_at", "last_trigger_at",
            "remaining_seconds", "relieved_levels", "pending_repetitions",
            "decay_paused", "recovery_since",
        ), optional=("attribution", "causes"), context="Moodlet episode")
        key = enum_value(entry["definition_id"], MoodletId, context="Moodlet family")
        definition = MOODLET_CATALOG.definitions[key]
        instance = integer_value(entry["instance_id"], minimum=1,
                                 maximum=next_id - 1, context="Moodlet instance")
        if key in families or instance in instances:
            raise ValueError("Duplicate Moodlet instance or family")
        level = integer_value(entry["level"], minimum=1,
                              maximum=len(definition.level_points),
                              context="Moodlet level")
        started = number_value(entry["started_at"], minimum=baseline,
                               maximum=elapsed, context="Moodlet start")
        trigger = number_value(entry["last_trigger_at"], minimum=started,
                               maximum=elapsed, context="Moodlet trigger")
        remaining = number_value(entry["remaining_seconds"], minimum=0,
                                 maximum=definition.decay_stage_seconds,
                                 context="Moodlet remaining stage")
        levels = entry["relieved_levels"]
        if not isinstance(levels, list) or len(levels) > len(definition.level_points):
            raise ValueError("Unbounded Moodlet relief usage")
        relieved = tuple(integer_value(v, minimum=1,
                                       maximum=len(definition.level_points),
                                       context="Moodlet relieved level")
                         for v in levels)
        if len(set(relieved)) != len(relieved) or (
            relieved and definition.relief_seconds == 0
        ):
            raise ValueError("Duplicate or ineligible Moodlet relief usage")
        parameters = definition.parameters
        repetitions = (
            parameters.escalation_pokes if isinstance(parameters, PokingParameters)
            else parameters.escalation_attempts
            if isinstance(parameters, PettingParameters) else 1
        )
        pending = integer_value(entry["pending_repetitions"], minimum=0,
                                maximum=repetitions - 1, context="Moodlet repetitions")
        if type(entry["decay_paused"]) is not bool:
            raise ValueError("Moodlet pause must be a boolean")
        recovery = (
            None if entry["recovery_since"] is None else number_value(
                entry["recovery_since"], minimum=started, maximum=elapsed,
                context="Moodlet recovery qualification",
            )
        )
        if definition.decay != MoodletDecay.STABLE_RECOVERY and recovery is not None:
            raise ValueError("Only poor-care Moodlets have stable recovery")
        if (definition.decay == MoodletDecay.QUIET_TIME and entry["decay_paused"]):
            raise ValueError("Quiet-time Moodlets cannot pause their ageing")
        causes = (_decode_causes(entry["causes"], started=started, trigger=trigger,
                                 key=key) if "causes" in entry else ())
        episodes.append(MoodletEpisode(
            instance, key, level, started, trigger, remaining, relieved, pending,
            entry["decay_paused"], recovery,
            enum_value(entry.get("attribution", "unknown"), MoodletAttribution,
                       context="Moodlet attribution"),
            causes,
        ))
        instances.add(instance)
        families.add(key)
    memory = InteractionMemory()
    if "interactions" in row:
        facts = object_fields(row["interactions"], (
            "poke_boundary_at", "petting_boundary_at", "petting_refused_until",
        ), optional=("food", "petting_excess_attempts", "petting_last_excess_at"),
            context="interaction evidence")
        anchors = tuple(None if facts[key] is None else number_value(
            facts[key], minimum=baseline, maximum=elapsed, context=key,
        ) for key in ("poke_boundary_at", "petting_boundary_at"))
        petting = MOODLET_CATALOG.definitions[MoodletId.CROWDED].parameters
        assert isinstance(petting, PettingParameters)
        deadline = number_value(facts["petting_refused_until"], minimum=0,
                                maximum=elapsed + max(petting.refusal_seconds),
                                context="petting refusal")
        food = (_decode_food(facts["food"], baseline, elapsed)
                if "food" in facts else FoodRepetitionMemory())
        attempts = integer_value(
            facts.get("petting_excess_attempts",
                      petting.accepted_excess_attempts + 1 if anchors[1] is not None
                      else 0), minimum=0, maximum=petting.accepted_excess_attempts + 1,
            context="petting additional attempts",
        )
        last = facts.get("petting_last_excess_at", anchors[1])
        last = (None if last is None else number_value(
            last, minimum=baseline, maximum=elapsed, context="last additional petting",
        ))
        if (attempts == 0) != (last is None):
            raise ValueError("Petting count and time must describe the same sequence")
        memory = InteractionMemory(anchors[0], anchors[1], deadline, food,
                                   attempts, last)
    poor_care = (decode_poor_care(row["poor_care"], baseline, elapsed)
                 if "poor_care" in row else None)
    return MoodletState(baseline, next_id, tuple(episodes), memory, poor_care)


def valid_moodlets(raw: Any, elapsed: float) -> bool:
    try:
        decode_moodlets(raw, elapsed)
    except (ValueError, TypeError, OverflowError):
        return False
    return True


def encode_moodlets(state: MoodletState) -> dict[str, Any]:
    encoded = dict(
        version=1, baseline=state.baseline, next_instance_id=state.next_instance_id,
        interactions=dict(
            poke_boundary_at=state.interactions.poke_boundary_at,
            petting_boundary_at=state.interactions.petting_boundary_at,
            petting_refused_until=state.interactions.petting_refused_until,
            petting_excess_attempts=state.interactions.petting_excess_attempts,
            petting_last_excess_at=state.interactions.petting_last_excess_at,
            food=dict(
                food_id=state.interactions.food.food_id,
                intakes=list(state.interactions.food.intakes),
                request_pending=state.interactions.food.request_pending,
                requested_at=state.interactions.food.requested_at,
                ignored_portions=state.interactions.food.ignored_portions,
            ),
        ),
        active=[dict(
            instance_id=e.instance_id, definition_id=e.definition_id.value,
            level=e.level, started_at=e.started_at, last_trigger_at=e.last_trigger_at,
            remaining_seconds=e.remaining_seconds,
            relieved_levels=list(e.relieved_levels),
            pending_repetitions=e.pending_repetitions, decay_paused=e.decay_paused,
            recovery_since=e.recovery_since,
            attribution=e.attribution.value,
            causes=[_encode_cause(c) for c in e.causes],
        ) for e in state.active],
    )
    if state.poor_care is not None:
        encoded["poor_care"] = encode_poor_care(state.poor_care)
    return encoded


def _decode_food(raw: Any, baseline: float, elapsed: float) -> FoodRepetitionMemory:
    row = object_fields(raw, ("food_id", "intakes", "request_pending", "requested_at",
                              "ignored_portions"), context="food repetition evidence")
    food = row["food_id"]
    if food is not None and (
        not isinstance(food, str) or food not in DEFAULT_CATALOG.foods
    ):
        raise ValueError("Unknown repetition food")
    count = BALANCE.integer("food", "consecutive_repeats_before_dislike") + 1
    if not isinstance(row["intakes"], list) or len(row["intakes"]) > count:
        raise ValueError("Unbounded food repetition history")
    intakes = tuple(number_value(t, minimum=baseline, maximum=elapsed,
                                 context="food intake") for t in row["intakes"])
    if tuple(sorted(intakes)) != intakes:
        raise ValueError("Unordered food intake evidence")
    if type(row["request_pending"]) is not bool:
        raise ValueError("Food request pending must be boolean")
    requested = None if row["requested_at"] is None else number_value(
        row["requested_at"], minimum=baseline, maximum=elapsed,
        context="communicated food request",
    )
    parameters = MOODLET_CATALOG.definitions[MoodletId.FOOD_MONOTONY].parameters
    assert isinstance(parameters, FoodMonotonyParameters)
    ignored = integer_value(row["ignored_portions"], minimum=0,
                            maximum=parameters.free_ignored_portions + 1,
                            context="ignored food requests")
    if (food is None and (intakes or requested is not None or row["request_pending"])
            or food is not None and not intakes
            or row["request_pending"] and requested is not None
            or ignored and requested is None):
        raise ValueError("Inconsistent food repetition evidence")
    return FoodRepetitionMemory(food, intakes, row["request_pending"],
                                requested, ignored)
