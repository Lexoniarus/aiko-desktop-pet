"""Presentation of already-derived impressions/objectives; never runs their rules."""

import math

from ...asset_paths import CONNECT_FOUR_DIR, MASTERMIND_DIR, PLAYING_CARDS_DIR
from ...pet.content import GERMAN_TEXT
from ...pet.wishes import WishId, WishObjective, WishTargetKind
from .contracts import MoodletView, WishView
from .moodlet_causes import cause_description

MOODLET_ICONS = {
    "food_fulfilled": "moodlet_food_fulfilled",
    "shared_play": "moodlet_shared_play",
    "pride": "moodlet_pride",
    "relief": "moodlet_relief",
    "connection": "moodlet_connection",
    "cheerful": "moodlet_cheerful",
    "enthusiastic": "moodlet_enthusiastic",
    "secure": "moodlet_secure",
    "poking": "moodlet_annoyed",
    "crowded": "moodlet_crowded",
    "food_monotony": "moodlet_food_monotony",
    "withheld": "moodlet_withheld",
    "disrupted": "moodlet_disrupted",
    "hunger_worn": "moodlet_hunger_worn",
    "exhaustion_irritated": "moodlet_exhaustion_irritated",
    "unstimulated": "moodlet_unstimulated",
    "lonely": "moodlet_lonely",
    "missing_closeness": "moodlet_missing_closeness",
    "disappointed": "moodlet_unstimulated",
    "food_wish_disregarded": "moodlet_food_monotony",
    "trusting": "moodlet_secure",
    "appreciated": "moodlet_connection",
    "optimistic": "moodlet_pride",
    "uncertain": "moodlet_unstimulated",
    "overlooked": "moodlet_lonely",
    "guarded": "moodlet_annoyed",
}
GAME_FILES = {
    "blackjack": PLAYING_CARDS_DIR / "card_spades_A.png",
    "connect_four": CONNECT_FOUR_DIR / "red.png",
    "mastermind": MASTERMIND_DIR / "blue.png",
}
GAME_ICONS = {"rock_paper_scissors": "game_rps", "tic_tac_toe": "game_tic_tac_toe"}


def duration_text(seconds: float) -> str:
    minutes = max(0, math.ceil(seconds / 60))
    if minutes >= 60:
        hours, rest = divmod(minutes, 60)
        return GERMAN_TEXT.format(
            "vn.hours_minutes" if rest else "vn.hours",
            **({"hours": str(hours), "minutes": str(rest)} if rest
               else {"hours": str(hours)}),
        )
    return GERMAN_TEXT.format("vn.minutes", minutes=str(minutes))


def moodlet_description(view: MoodletView) -> str:
    value = view.value
    parts = [
        view.label + " · " + GERMAN_TEXT.format(
            "vn.moodlet_strength", level=str(value.level),
            points=f"{value.mood_points:+d}",
        ),
        view.description,
        GERMAN_TEXT.format(f"vn.attribution.{value.attribution}"),
    ]
    if value.decay_paused:
        parts.append(GERMAN_TEXT.format("vn.decay_paused"))
    if value.recovery_wait_seconds is not None and value.recovery_wait_seconds > 0:
        parts.append(
            GERMAN_TEXT.format(
                "vn.recovery_wait", time=duration_text(value.recovery_wait_seconds)
            )
        )
    parts.append(
        GERMAN_TEXT.format(
            "vn.decay_work",
            stage=duration_text(value.remaining_stage_seconds),
            total=duration_text(value.remaining_decay_seconds),
        )
    )
    parts.extend(GERMAN_TEXT.format(
        "vn.cause_entry", number=str(index), cause=cause_description(cause),
    ) for index, cause in enumerate(value.causes, 1))
    return "\n".join(parts)


def wish_progress(view: WishView, *, compact: bool = False) -> str:
    game = view.value.game
    if game is None:
        return ""
    wins_goal = (view.value.goal is not None
                 and view.value.goal.objective == WishObjective.TOTAL_WINS)
    if compact:
        return GERMAN_TEXT.format(
            "vn.wins_short" if wins_goal else "vn.rounds_short",
            completed=str(game.wins if wins_goal else game.completed_rounds),
            required=str(game.required_count),
        )
    return GERMAN_TEXT.format(
        "vn.game_wins_progress" if wins_goal else "vn.game_progress",
        completed=str(game.completed_rounds), required=str(game.required_count),
        wins=str(game.wins), losses=str(game.losses),
    )


def wish_description(view: WishView) -> str:
    parts = [
        view.label,
        view.target_label,
        view.description,
        wish_progress(view),
        (GERMAN_TEXT.format("vn.wish_pinned") if view.value.pinned
         else GERMAN_TEXT.format(
             "vn.wish_remaining", time=duration_text(view.value.remaining_seconds)
         )),
        GERMAN_TEXT.format("vn.wish_controls"),
        GERMAN_TEXT.format(
            "vn.wish_spoken" if view.value.expressed else "vn.wish_inner"
        ),
        view.restriction_label,
    ]
    return "\n".join(p for p in parts if p)


def wish_icon(view: WishView) -> str:
    if view.value.target_kind == WishTargetKind.GAME:
        return (view.value.target_id if view.value.target_id in GAME_FILES
                else GAME_ICONS.get(view.value.target_id, "status_fun"))
    if view.value.target_kind == WishTargetKind.SOCIAL:
        return {WishId.SINGLE: "wish_single", WishId.TWO_PARTS: "wish_twopart",
                WishId.FACT: "wish_fact"}.get(view.value.definition_id, "status_social")
    return {
        WishId.PET: "action_pet",
        WishId.CHAT: "status_social",
        WishId.SINGLE: "wish_single",
        WishId.TWO_PARTS: "wish_twopart",
        WishId.FACT: "wish_fact",
    }.get(view.value.definition_id, "food")


def wish_badge(view: WishView) -> str | None:
    if view.value.definition_id in (WishId.WIN_ROUND, WishId.WIN_OVERALL):
        return "moodlet_pride"
    if view.value.definition_id in (WishId.AVOID_ROUND_LOSS, WishId.AVOID_OVERALL_LOSS):
        return "wish_protection_shield"
    return None
