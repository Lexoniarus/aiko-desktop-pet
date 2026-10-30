"""Semantic facial presentation, independent of care and body movement."""

from __future__ import annotations

from enum import StrEnum

from ..emotions import EmotionalState


class Expression(StrEnum):
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    QUESTIONING = "questioning"
    WORRIED = "worried"
    DOWNCAST = "downcast"
    FIRM = "firm"


EXPRESSION_CLIPS = {
    Expression.NEUTRAL: "rest-neutral",
    Expression.POSITIVE: "expression-positive",
    Expression.QUESTIONING: "expression-questioning",
    Expression.WORRIED: "expression-worried",
    Expression.DOWNCAST: "expression-downcast",
    Expression.FIRM: "expression-firm",
}


def mood_expression(feeling: EmotionalState) -> Expression:
    """Project the canonical feeling; physical tiredness is not sadness."""
    if feeling in (EmotionalState.CHEERFUL, EmotionalState.PROUD,
                   EmotionalState.CAREFREE):
        return Expression.POSITIVE
    if feeling in (EmotionalState.DOWNCAST, EmotionalState.LONELY):
        return Expression.DOWNCAST
    if feeling in (EmotionalState.IRRITATED, EmotionalState.CROWDED,
                   EmotionalState.FRUSTRATED):
        return Expression.FIRM
    if feeling in (EmotionalState.TENSE, EmotionalState.RESERVED):
        return Expression.WORRIED
    return Expression.NEUTRAL


def event_expression(event: str) -> Expression | None:
    """Only explicitly authored semantic events, never sentiment from words."""
    return {
        "game_ttt_block": Expression.WORRIED,
        "game_ttt_player_threat": Expression.WORRIED,
        "game_ttt_finish": Expression.POSITIVE,
        "game_ttt_fork": Expression.POSITIVE,
        "game_ttt_threat": Expression.POSITIVE,
        "game_ttt_balanced": Expression.QUESTIONING,
        "game_ttt_mistake": Expression.WORRIED,
        "game_ttt_mistake_draw": Expression.WORRIED,
        "game_ttt_forced_player": Expression.WORRIED,
        "game_ttt_forced_aiko": Expression.POSITIVE,
        "game_ttt_player_win": Expression.DOWNCAST,
        "game_ttt_aiko_win": Expression.POSITIVE,
        "game_ttt_draw": Expression.QUESTIONING,
        "cursor_notice_playful": Expression.QUESTIONING,
        "cursor_play_start": Expression.QUESTIONING,
        "cursor_play_more": Expression.POSITIVE,
        "cursor_play_peak": Expression.POSITIVE,
        "cursor_warning_near_fast": Expression.WORRIED,
        "cursor_fear_response": Expression.WORRIED,
        "rapid_click": Expression.FIRM,
        "sleep_click": Expression.FIRM,
        "game_greeting": Expression.POSITIVE,
        "game_ttt_greeting": Expression.QUESTIONING,
        "game_blackjack_greeting": Expression.QUESTIONING,
        "game_c4_greeting": Expression.QUESTIONING,
        "game_mm_greeting": Expression.QUESTIONING,
        "game_player_win": Expression.DOWNCAST,
        "game_round_player_win": Expression.DOWNCAST,
        "game_c4_player_win": Expression.DOWNCAST,
        "game_aiko_win": Expression.POSITIVE,
        "game_round_aiko_win": Expression.POSITIVE,
        "game_c4_aiko_win": Expression.POSITIVE,
        "game_draw": Expression.QUESTIONING,
        "game_round_draw": Expression.QUESTIONING,
        "game_c4_draw": Expression.QUESTIONING,
        "game_c4_block": Expression.POSITIVE,
        "game_c4_blocked": Expression.QUESTIONING,
        "game_mm_player_win": Expression.POSITIVE,
        "game_mm_aiko_win": Expression.WORRIED,
        "game_mm_progress": Expression.QUESTIONING,
        "game_mm_last": Expression.WORRIED,
        "game_quiz_greeting": Expression.QUESTIONING,
        "game_quiz_correct": Expression.POSITIVE,
        "game_quiz_incorrect": Expression.WORRIED,
        "game_quiz_encourage": Expression.POSITIVE,
        "game_quiz_finish": Expression.POSITIVE,
        "game_quiz_rolebreak": Expression.POSITIVE,
    }.get(event)
