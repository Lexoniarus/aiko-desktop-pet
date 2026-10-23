"""Pure outcomes for already admitted care and assigned game/social attempts."""

from dataclasses import replace
from typing import Literal, Mapping

from .moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletGameResult,
    MoodletOutcome,
    MoodletWishCause,
)
from .wish_matching import assign_activity_wish, wish_matches_activity
from .wishes import (
    MAX_WISH_ROUND_RECEIPTS,
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishDefinition,
    WishGoal,
    WishId,
    WishObjective,
    WishResolution,
    WishState,
    wish_refresh_deadline,
)


def wish_cause(
    wish: ActiveWish, *, elapsed: float, event_id: str, outcome: MoodletOutcome,
    failed: bool = False, target_id: str | None = None,
    object_id: str | None = None, game: MoodletGameResult | None = None,
) -> MoodletCause:
    goal = wish.goal_snapshot
    return MoodletCause(
        MoodletCauseKind.WISH_FAILED if failed else MoodletCauseKind.WISH_FULFILLED,
        elapsed, event_id,
        wish=MoodletWishCause(wish.instance_id, wish.definition_id.value,
                             wish.target_id, goal.objective.value, goal.required_count,
                             target=wish.target),
        target_id=wish.target_id if target_id is None else target_id,
        outcome=outcome, object_id=object_id, game=game,
    )


def fulfill_activity_wish(
    state: WishState, area: WishArea, target_id: str, *, elapsed: float,
    definitions: Mapping[WishId, WishDefinition], instance_id: int | None = None,
    object_id: str | None = None, event_id: str | None = None,
    started_at: float | None = None,
) -> WishResolution:
    """Resolve the admitted identity; a stale assignment never chooses a fallback."""
    wish = (assign_activity_wish(state, area, target_id, elapsed=elapsed,
                                 definitions=definitions) if instance_id is None
            else next((w for w in state.active if w.instance_id == instance_id
                       and w.is_active_at(elapsed)
                       and w.goal_snapshot.objective != WishObjective.FOOD_HANDOVER
                       and wish_matches_activity(w, area, target_id,
                                                  definitions=definitions)), None))
    if (wish is None or started_at is not None
            and not wish.created_at <= started_at <= elapsed):
        return WishResolution(state)
    return _retire_wish(
        state, wish, definitions[wish.definition_id], elapsed=elapsed,
        cause=wish_cause(wish, elapsed=elapsed,
                          event_id=event_id or f"wish:{wish.instance_id}:fulfilled",
                          target_id=target_id,
                          outcome=MoodletOutcome.INTAKE if area == WishArea.FOOD
                          else MoodletOutcome.COMPLETED, object_id=object_id),
    )


def fulfill_food_handover_wish(
    state: WishState, food_id: str, *, elapsed: float, object_id: str,
    definitions: Mapping[WishId, WishDefinition],
) -> WishResolution:
    """A qualified personal offer resolves avoidance, never ordinary intake wishes."""
    wish = next((w for w in state.active
                 if w.goal_snapshot.objective == WishObjective.FOOD_HANDOVER
                 and definitions[w.definition_id].area == WishArea.FOOD
                 and food_id in definitions[w.definition_id].targets
                 and w.is_active_at(elapsed)), None)
    if wish is None:
        return WishResolution(state)
    return _retire_wish(
        state, wish, definitions[wish.definition_id], elapsed=elapsed,
        cause=wish_cause(wish, elapsed=elapsed,
                          event_id=f"wish:{wish.instance_id}:handover",
                          outcome=MoodletOutcome.HANDOVER, target_id=food_id,
                          object_id=object_id),
    )


def _retire_wish(
    state: WishState, wish: ActiveWish, fulfilled: WishDefinition | None,
    *, elapsed: float, cause: MoodletCause | None = None,
) -> WishResolution:
    return WishResolution(replace(
        state, active=tuple(w for w in state.active
                            if w.instance_id != wish.instance_id),
        refresh_at=wish_refresh_deadline(state, elapsed),
    ), fulfilled, cause)


def _game_result(
    goal: WishGoal, progress: GameWishProgress, outcome: Literal["win", "loss", "draw"],
) -> tuple[bool, bool, MoodletOutcome]:
    """Completion and success are properties of the original goal, not its ID."""
    objective = goal.objective
    if objective in (WishObjective.RETRY_WIN, WishObjective.NEXT_WIN):
        won = outcome == "win"
        return won or objective == WishObjective.NEXT_WIN, won, MoodletOutcome(outcome)
    if objective == WishObjective.NEXT_NON_LOSS:
        return True, outcome != "loss", MoodletOutcome(outcome)
    if objective == WishObjective.TOTAL_WINS:
        return progress.wins >= goal.required_count, True, MoodletOutcome.WIN
    if objective in (WishObjective.SESSION_ROUNDS, WishObjective.TOTAL_ROUNDS):
        return (progress.completed_rounds >= goal.required_count, True,
                MoodletOutcome.COMPLETED)
    if objective not in (WishObjective.BLOCK_MAJORITY, WishObjective.BLOCK_NON_LOSS):
        raise ValueError("Unsupported game wish objective")
    result = (MoodletOutcome.WIN if progress.wins > progress.losses
              else MoodletOutcome.DRAW if progress.wins == progress.losses
              else MoodletOutcome.LOSS)
    success = (result == MoodletOutcome.WIN or result == MoodletOutcome.DRAW
               and objective == WishObjective.BLOCK_NON_LOSS)
    return progress.completed_rounds >= goal.required_count, success, result


def progress_game_wish(
    state: WishState, instance_id: int, *, game_id: str, session_id: str,
    round_id: str, started_at: float, elapsed: float,
    outcome: Literal["win", "loss", "draw"],
    definitions: Mapping[WishId, WishDefinition],
) -> WishResolution:
    """One real qualifying round, from Aiko's perspective; no session score."""
    wish = next((w for w in state.active if w.instance_id == instance_id), None)
    if (wish is None or not wish_matches_activity(
                wish, WishArea.GAMES, game_id, definitions=definitions,
            )
            or not wish.created_at <= started_at <= elapsed
            or not wish.is_active_at(elapsed)
            or round_id in wish.game.round_ids):
        return WishResolution(state)
    definition, goal = definitions[wish.definition_id], wish.goal_snapshot
    before = wish.game
    if (goal.objective == WishObjective.RETRY_WIN
            or goal.objective == WishObjective.SESSION_ROUNDS
            and before.session_id != session_id):
        before = GameWishProgress()
    if before.completed_rounds >= 2**63 - 1:
        raise ValueError("Wish attempt count exhausted")
    progress = GameWishProgress(
        (*before.round_ids, round_id)[-MAX_WISH_ROUND_RECEIPTS:],
        before.wins + (outcome == "win"), before.losses + (outcome == "loss"),
        session_id if goal.objective == WishObjective.SESSION_ROUNDS else None,
        before.completed_rounds + 1,
    )
    finished, success, result = _game_result(goal, progress, outcome)
    if finished:
        disappointed = (not success and goal.objective in (
            WishObjective.NEXT_NON_LOSS, WishObjective.BLOCK_NON_LOSS,
        ))
        cause = (wish_cause(
            wish, elapsed=elapsed, event_id=round_id, outcome=result,
            failed=disappointed, target_id=game_id, game=MoodletGameResult(
                MoodletOutcome(outcome), progress.completed_rounds,
                progress.wins, progress.losses,
            ),
        ) if success or disappointed else None)
        return _retire_wish(state, wish, definition if success else None,
                            elapsed=elapsed, cause=cause)
    return WishResolution(replace(state, active=tuple(
        replace(w, game=progress) if w.instance_id == instance_id else w
        for w in state.active
    )))
