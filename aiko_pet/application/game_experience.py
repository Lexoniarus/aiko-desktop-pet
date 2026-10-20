"""Translate individual minigames into one game-agnostic care experience.

Session scores live in the game and its window only. This coordinator receives
actual round boundaries for wishes and the immutable ordinary-care summary at
close. Only bounded wish progress persists; the current round attempt is transient.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..games.contracts import GameId, GameRoundEvent, RoundOutcome, SessionSummary
from ..games.rock_paper_scissors import Score
from ..pet.fun import GameExperience
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.state import PetState
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import WishArea
from .active_time import (
    ActiveSessionClock,
    SessionInputs,
    TimeProgression,
    advance_session_time,
)


def experience_from_rock_paper_scissors(score: Score) -> GameExperience:
    """The existing RPS score is from the *player's* perspective."""
    return experience_from_session(SessionSummary(
        GameId.ROCK_PAPER_SCISSORS, score.wins, score.losses, score.draws,
    ))


def experience_from_session(summary: SessionSummary) -> GameExperience:
    """Translate once from player results to Aiko's care experience."""
    return GameExperience(
        game_id=summary.game_id.value,
        completed_units=summary.games,
        successful_units=summary.losses,
        neutral_units=summary.draws,
        setback_units=summary.wins,
    )


@dataclass(frozen=True, slots=True)
class GameExperienceOutcome:
    """Only the effect survives; no round score belongs in pet storage."""

    fun_gained: float
    fun_after: float


@dataclass(frozen=True, slots=True)
class _WishRoundAttempt:
    start: GameRoundEvent
    elapsed: float
    wish_instance_id: int | None


class GameExperienceCoordinator:
    """Owner-thread use case for completed games, independent of Tk windows."""

    def __init__(
        self, state: PetState, mind: PetMind, adaptive: AdaptiveRoutine, *,
        clock: ActiveSessionClock,
        progression: TimeProgression | None = None,
        arrangement_ready: Callable[[], bool] = lambda: False,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock
        self._progression = progression
        self._arrangement_ready = arrangement_ready
        self._round: _WishRoundAttempt | None = None

    def observe_round(self, event: GameRoundEvent, inputs: SessionInputs) -> None:
        """Observe actual start/result; capture the existing wish before play."""
        if event.outcome is None:
            if self._round is not None and self._round.start == event:
                return
            advance_session_time(
                self._state, self._clock, inputs, progression=self._progression,
            )
            wish = next((w for w in self._state.wishes.active
                         if WISH_CATALOG.definitions[w.definition_id].area
                         == WishArea.GAMES
                         and w.target_id == event.game_id.value), None)
            self._round = _WishRoundAttempt(
                event, self._state.lived_seconds, wish.instance_id if wish else None,
            )
            return
        pending = self._round
        if (pending is None or pending.start.game_id != event.game_id
                or pending.start.identity != event.identity):
            return
        advance_session_time(
            self._state, self._clock, inputs, progression=self._progression,
        )
        if pending.wish_instance_id is not None:
            outcome: RoundOutcome = ("loss" if event.outcome == "win" else
                                     "win" if event.outcome == "loss" else "draw")
            self._state.complete_wish_round(
                pending.wish_instance_id, game_id=event.game_id.value,
                session_id=event.session_id, round_id=event.identity,
                started_at=pending.elapsed, outcome=outcome,
            )
        self._round = None  # Retire after a successful commit, before UI callbacks.

    def complete(
        self, experience: GameExperience, inputs: SessionInputs,
    ) -> GameExperienceOutcome:
        """Account for elapsed awake time, then commit exactly one session."""
        self._round = None
        if experience.completed_units == 0:
            return GameExperienceOutcome(0.0, self._state.fun)
        advance_session_time(
            self._state, self._clock, inputs, progression=self._progression,
        )
        gained = self._state.record_game_experience(
            experience, now=inputs.wall_time,
            arrangement_ready=self._arrangement_ready(),
        )
        self._adaptive.note_interaction(inputs.wall_time)
        self._mind.after_care("play", inputs.monotonic_time)
        return GameExperienceOutcome(gained, self._state.fun)
