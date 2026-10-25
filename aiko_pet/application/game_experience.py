"""Translate individual minigames into one game-agnostic care experience.

Session scores live in the game and its window only. This coordinator receives
actual round boundaries for wishes and the immutable ordinary-care summary at
close. Bounded wish progress and actual round evidence persist in Pet; the
current round attempt is transient.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..games.contracts import GameId, GameResult, GameRoundEvent, SessionSummary
from ..games.rock_paper_scissors import Score
from ..pet.fun import GameExperience
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.state import PetState
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wish_matching import assign_activity_wish
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
        self._last_round: GameRoundEvent | None = None
        self._quiz_session: str | None = None
        self._quiz_units = 0
        self._quiz_fun = 0.0

    def observe_round(self, event: GameRoundEvent, inputs: SessionInputs) -> None:
        """Observe actual start/result; capture the existing wish before play."""
        if event.outcome is None:
            if self._round is not None and self._round.start == event:
                return
            advance_session_time(
                self._state, self._clock, inputs, progression=self._progression,
            )
            wish = assign_activity_wish(
                self._state.wishes, WishArea.GAMES, event.game_id.value,
                elapsed=self._state.lived_seconds, definitions=WISH_CATALOG.definitions,
            )
            self._round = _WishRoundAttempt(
                event, self._state.lived_seconds, wish.instance_id if wish else None,
            )
            if event.game_id is GameId.QUIZ and self._quiz_session != event.session_id:
                self._quiz_session = event.session_id
                self._quiz_units = 0
                self._quiz_fun = 0.0
            return
        pending = self._round
        if (pending is None or pending.start.game_id != event.game_id
                or pending.start.identity != event.identity):
            return
        advance_session_time(
            self._state, self._clock, inputs, progression=self._progression,
        )
        outcome: GameResult = (
            "completed" if event.outcome == "completed" else
            "loss" if event.outcome == "win" else
            "win" if event.outcome == "loss" else "draw"
        )
        recorded = self._state.record_completed_game_round(
            game_id=event.game_id.value, round_id=event.identity, outcome=outcome,
        )
        if not recorded:
            self._round = None
            return
        if pending.wish_instance_id is not None:
            self._state.complete_wish_round(
                pending.wish_instance_id, game_id=event.game_id.value,
                session_id=event.session_id, round_id=event.identity,
                started_at=pending.elapsed, outcome=outcome, game_details=event.details,
            )
        self._state.finish_game_round_experience(
            game_id=event.game_id.value, round_id=event.identity,
            game_details=event.details,
        )
        if outcome == "completed":
            # Quiz rewards settle now, using one cumulative window-session budget.
            gained = self._state.record_game_experience(
                GameExperience("quiz", self._quiz_units + 1),
                now=inputs.wall_time, arrangement_ready=self._arrangement_ready(),
                previous_units=self._quiz_units, awarded_fun=self._quiz_fun,
            )
            self._quiz_units += 1
            self._quiz_fun += gained
            self._state.complete_play_session(
                game_id="quiz", session_id=event.session_id, round_id=event.identity,
            )
            self._adaptive.note_interaction(inputs.wall_time)
            self._mind.record_accepted_care("play", inputs.monotonic_time)
        self._last_round = event
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
        last, self._last_round = self._last_round, None
        if last is not None and last.game_id.value == experience.game_id:
            self._state.complete_play_session(
                game_id=experience.game_id, session_id=last.session_id,
                round_id=last.identity, game_details=last.details,
            )
        self._adaptive.note_interaction(inputs.wall_time)
        self._mind.record_accepted_care("play", inputs.monotonic_time)
        return GameExperienceOutcome(gained, self._state.fun)
