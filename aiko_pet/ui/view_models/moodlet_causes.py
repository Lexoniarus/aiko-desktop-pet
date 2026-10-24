"""Localize actual active-episode receipts without inventing events or tiers."""

from ...pet.content import GERMAN_TEXT
from ...pet.food import FOOD_CATALOG
from ...pet.moodlets import MoodletAttribution, MoodletCause, MoodletCauseKind
from ...pet.wishes import WishGoal, WishId, WishObjective, wish_text_key


def _target_label(target: str) -> str:
    for key in (f"need.{target}", f"moodlet.{target}.label"):
        if key in GERMAN_TEXT.messages:
            return GERMAN_TEXT.format(key)
    if target in FOOD_CATALOG:
        return FOOD_CATALOG[target].display_name
    game_key = f"game.name.{target}"
    if game_key in GERMAN_TEXT.messages:
        return GERMAN_TEXT.format(game_key)
    social_key = f"social.name.{target}"
    if social_key in GERMAN_TEXT.messages:
        return GERMAN_TEXT.format(social_key)
    if target in ("chat", "pet"):
        return GERMAN_TEXT.format(f"wish.{target}.label")
    return GERMAN_TEXT.format("vn.cause_unknown_target")


def cause_description(cause: MoodletCause) -> str:
    """Compact actual goal/result; full evidence stays in the read value."""
    parts = [GERMAN_TEXT.format(f"vn.cause.{cause.kind}")]
    wish = cause.wish
    if wish is not None:
        goal = WishGoal(WishObjective(wish.objective), wish.required_count)
        parts.append(GERMAN_TEXT.format(
            "vn.cause_wish",
            wish=GERMAN_TEXT.format(wish_text_key(
                WishId(wish.definition_id), goal, "label",
            )),
            target=_target_label(wish.target_id),
        ))
        if goal.required_count > 1:
            parts.append(GERMAN_TEXT.format(
                "vn.cause_goal_count", count=str(goal.required_count),
            ))
    if (cause.target_id is not None
            and (wish is None or cause.target_id != wish.target_id)):
        parts.append(GERMAN_TEXT.format(
            "vn.cause_target", target=_target_label(cause.target_id),
        ))
    if (cause.kind != MoodletCauseKind.LEGACY
            and (cause.game is None or cause.game.round_outcome != cause.outcome)):
        parts.append(GERMAN_TEXT.format(
            "vn.cause_result",
            result=GERMAN_TEXT.format(f"vn.outcome.{cause.outcome}"),
        ))
    if cause.attribution != MoodletAttribution.UNKNOWN:
        parts.append(GERMAN_TEXT.format(f"vn.cause_by.{cause.attribution}"))
    summary = " · ".join(parts)
    if cause.game is None:
        return summary
    game = cause.game
    return summary + "\n" + GERMAN_TEXT.format(
        "vn.cause_game",
        round=GERMAN_TEXT.format(f"vn.outcome.{game.round_outcome}"),
        rounds=str(game.completed_rounds), wins=str(game.wins), losses=str(game.losses),
    )
