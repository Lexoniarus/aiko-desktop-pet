"""Bounded original wish, handover and qualifying-period facts inside Moodlet causes."""

from typing import Any

from ..games.contracts import (
    BlackjackDecisionReason,
    BlackjackDetails,
    GameId,
    GameResultDetails,
    RockPaperScissorsDetails,
    RockPaperScissorsMove,
)
from ..pet.catalog_validation import (
    enum_value,
    integer_value,
    number_value,
    object_fields,
)
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlets import (
    MAX_MOODLET_CAUSES,
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletGameResult,
    MoodletGroup,
    MoodletId,
    MoodletOutcome,
    MoodletWishCause,
)
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import WishArea, WishId, WishTargetMode
from .care_evidence_codec import decode_period_summary, encode_period_summary
from .wish_snapshot_codec import (
    decode_wish_goal,
    decode_wish_target,
    encode_wish_target,
)


def _token(raw: Any) -> str:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise ValueError("Invalid Moodlet cause identity")
    return raw


def _wish_cause(raw: Any) -> MoodletWishCause:
    row = object_fields(
        raw,
        ("instance_id", "definition_id", "target_id", "objective", "required_count"),
        optional=("target",),
        context="Moodlet source wish",
    )
    key = enum_value(row["definition_id"], WishId, context="Moodlet source wish")
    goal = decode_wish_goal(
        dict(objective=row["objective"], required_count=row["required_count"]), key
    )
    target = (
        None if row.get("target") is None else decode_wish_target(row["target"], key)
    )
    reference = row["target_id"]
    if (
        not isinstance(reference, str)
        or target is None
        and reference not in WISH_CATALOG.definitions[key].targets
        or target is not None
        and reference != (target.target_id or "")
    ):
        raise ValueError("Incompatible Moodlet source wish target")
    return MoodletWishCause(
        integer_value(
            row["instance_id"],
            minimum=1,
            maximum=2**63 - 2,
            context="Moodlet source wish instance",
        ),
        key.value,
        reference,
        goal.objective.value,
        goal.required_count,
        target,
    )


def _game_details(raw: Any) -> GameResultDetails:
    if isinstance(raw, dict) and raw.get("game_id") == GameId.BLACKJACK.value:
        row = object_fields(
            raw, ("game_id", "player_total", "aiko_total", "reason"),
            context="Moodlet Blackjack details",
        )
        return BlackjackDetails(
            integer_value(row["player_total"], minimum=4, maximum=30,
                          context="player Blackjack total"),
            integer_value(row["aiko_total"], minimum=4, maximum=26,
                          context="Aiko Blackjack total"),
            enum_value(row["reason"], BlackjackDecisionReason,
                       context="Blackjack decision reason"),
        )
    row = object_fields(
        raw, ("game_id", "player_move", "aiko_move"), context="Moodlet game details",
    )
    if row["game_id"] != GameId.ROCK_PAPER_SCISSORS.value:
        raise ValueError("Unsupported Moodlet game details")
    return RockPaperScissorsDetails(
        enum_value(row["player_move"], RockPaperScissorsMove, context="player move"),
        enum_value(row["aiko_move"], RockPaperScissorsMove, context="Aiko move"),
    )


def decode_moodlet_causes(
    raw: Any,
    *,
    started: float,
    trigger: float,
    key: MoodletId,
    baseline: float,
) -> tuple[MoodletCause, ...]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_MOODLET_CAUSES:
        raise ValueError("Moodlet needs one to three bounded causes")
    causes = []
    receipts: set[tuple[MoodletCauseKind, str | None, int | None]] = set()
    previous = started
    for value in raw:
        row = object_fields(
            value,
            (
                "kind",
                "occurred_at",
                "event_id",
                "attribution",
                "wish",
                "target_id",
                "outcome",
                "object_id",
            ),
            optional=("game", "level", "period", "handed_over_at", "game_details"),
            context="Moodlet cause",
        )
        kind = enum_value(row["kind"], MoodletCauseKind, context="Moodlet cause kind")
        at = number_value(
            row["occurred_at"],
            minimum=previous,
            maximum=trigger,
            context="Moodlet cause time",
        )
        event = None if row["event_id"] is None else _token(row["event_id"])
        target = None if row["target_id"] is None else _token(row["target_id"])
        object_id = None if row["object_id"] is None else _token(row["object_id"])
        outcome = enum_value(row["outcome"], MoodletOutcome, context="Moodlet outcome")
        wish = None if row["wish"] is None else _wish_cause(row["wish"])
        game = None if row.get("game") is None else _game_result(row["game"])
        period = (
            None
            if row.get("period") is None
            else decode_period_summary(row["period"], baseline, at)
        )
        handover = (
            None
            if row.get("handed_over_at") is None
            else number_value(
                row["handed_over_at"],
                minimum=0,
                maximum=at,
                context="original handover time",
            )
        )
        if (
            (kind == MoodletCauseKind.LONG_TERM) != (period is not None)
            or period is not None
            and (
                MOODLET_CATALOG.definitions[key].group != MoodletGroup.LONG_TERM
                or wish is not None
                or target is not None
                or object_id is not None
                or outcome != MoodletOutcome.COMPLETED
            )
            or handover is not None
            and (
                wish is None
                or outcome != MoodletOutcome.HANDOVER
                or WISH_CATALOG.definitions[WishId(wish.definition_id)].area
                != WishArea.FOOD
            )
        ):
            raise ValueError("Incompatible Moodlet period or handover facts")
        # Read the superseded per-stage metadata without using it to discard
        # real receipts. New saves retain only the canonical chronological list.
        if row.get("level") is not None:
            integer_value(
                row["level"],
                minimum=1,
                maximum=len(MOODLET_CATALOG.definitions[key].level_points),
                context="Moodlet cause stage",
            )
            if kind == MoodletCauseKind.LEGACY:
                raise ValueError("Legacy cause cannot have a known stage")
        if (
            kind == MoodletCauseKind.LEGACY
            and (
                len(raw) != 1
                or event is not None
                or wish is not None
                or target is not None
                or object_id is not None
                or game is not None
                or outcome != MoodletOutcome.UNKNOWN
            )
            or kind != MoodletCauseKind.LEGACY
            and event is None
            or (kind in (MoodletCauseKind.WISH_FULFILLED, MoodletCauseKind.WISH_FAILED))
            != (wish is not None)
        ):
            raise ValueError("Inconsistent Moodlet cause evidence")
        if wish is not None:
            definition = WISH_CATALOG.definitions[WishId(wish.definition_id)]
            if game is not None and definition.area != WishArea.GAMES:
                raise ValueError("Game result requires a game wish cause")
            if kind == MoodletCauseKind.WISH_FULFILLED:
                if (
                    definition.fulfillment_moodlet != key
                    or outcome == MoodletOutcome.UNKNOWN
                ):
                    raise ValueError("Incompatible Moodlet fulfillment cause")
            elif key == MoodletId.FOOD_WISH_DISREGARDED:
                if (
                    definition.id != WishId.AVOID_FOOD
                    or outcome != MoodletOutcome.HANDOVER
                    or wish.target is None
                    or wish.target.mode != WishTargetMode.EXCLUDE
                    or target != wish.target.target_id
                ):
                    raise ValueError("Incompatible disregarded food-wish cause")
            elif (
                key != MoodletId.DISAPPOINTED
                or outcome != MoodletOutcome.LOSS
                or definition.id
                not in (WishId.AVOID_ROUND_LOSS, WishId.AVOID_OVERALL_LOSS)
            ):
                raise ValueError("Incompatible Moodlet failure cause")
            if kind == MoodletCauseKind.WISH_FULFILLED and wish.target is not None:
                if target is None or not wish.target.matches(
                    definition.target_kind, target
                ):
                    raise ValueError(
                        "Actual outcome does not match original wish target"
                    )
            if definition.area == WishArea.FOOD:
                if target is not None and target not in DEFAULT_CATALOG.foods:
                    raise ValueError("Unknown actual food in Moodlet cause")
            elif (
                wish.target is None and target is not None and target != wish.target_id
            ):
                raise ValueError("Mismatched actual Moodlet target")
        elif game is not None:
            raise ValueError("Game result requires an original wish")
        cause = MoodletCause(
            kind,
            at,
            event,
            enum_value(
                row["attribution"],
                MoodletAttribution,
                context="Moodlet cause attribution",
            ),
            wish,
            target,
            outcome,
            object_id,
            game,
            period,
            handover,
            None if row.get("game_details") is None else _game_details(
                row["game_details"],
            ),
        )
        if cause.receipt in receipts:
            raise ValueError("Duplicate Moodlet cause receipt")
        receipts.add(cause.receipt)
        causes.append(cause)
        previous = at
    return tuple(causes)


def _game_result(raw: Any) -> MoodletGameResult:
    row = object_fields(
        raw,
        ("round_outcome", "completed_rounds", "wins", "losses"),
        context="Moodlet game result",
    )
    outcome = enum_value(
        row["round_outcome"], MoodletOutcome, context="Moodlet settled round outcome"
    )
    rounds = integer_value(
        row["completed_rounds"],
        minimum=1,
        maximum=2**63 - 1,
        context="Moodlet completed rounds",
    )
    wins = integer_value(
        row["wins"], minimum=0, maximum=rounds, context="Moodlet game wins"
    )
    losses = integer_value(
        row["losses"], minimum=0, maximum=rounds - wins, context="Moodlet game losses"
    )
    if (
        outcome not in (MoodletOutcome.WIN, MoodletOutcome.LOSS, MoodletOutcome.DRAW,
                        MoodletOutcome.COMPLETED)
        or outcome == MoodletOutcome.WIN
        and wins == 0
        or outcome == MoodletOutcome.LOSS
        and losses == 0
        or outcome == MoodletOutcome.DRAW
        and rounds == wins + losses
    ):
        raise ValueError("Inconsistent Moodlet settled game result")
    return MoodletGameResult(outcome, rounds, wins, losses)


def encode_moodlet_cause(cause: MoodletCause) -> dict[str, Any]:
    wish = cause.wish
    encoded: dict[str, Any] = dict(
        kind=cause.kind.value,
        occurred_at=cause.occurred_at,
        event_id=cause.event_id,
        attribution=cause.attribution.value,
        target_id=cause.target_id,
        outcome=cause.outcome.value,
        object_id=cause.object_id,
        period=None if cause.period is None else encode_period_summary(cause.period),
        handed_over_at=cause.handed_over_at,
        game=None
        if cause.game is None
        else dict(
            round_outcome=cause.game.round_outcome.value,
            completed_rounds=cause.game.completed_rounds,
            wins=cause.game.wins,
            losses=cause.game.losses,
        ),
        wish=None
        if wish is None
        else dict(
            instance_id=wish.instance_id,
            definition_id=wish.definition_id,
            target_id=wish.target_id,
            objective=wish.objective,
            required_count=wish.required_count,
            target=None if wish.target is None else encode_wish_target(wish.target),
        ),
    )
    if isinstance(cause.game_details, RockPaperScissorsDetails):
        encoded["game_details"] = dict(
            game_id=GameId.ROCK_PAPER_SCISSORS.value,
            player_move=cause.game_details.player_move.value,
            aiko_move=cause.game_details.aiko_move.value,
        )
    elif isinstance(cause.game_details, BlackjackDetails):
        encoded["game_details"] = dict(
            game_id=GameId.BLACKJACK.value,
            player_total=cause.game_details.player_total,
            aiko_total=cause.game_details.aiko_total,
            reason=cause.game_details.reason.value,
        )
    return encoded
