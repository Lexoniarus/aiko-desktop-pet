"""Translate individual minigames into one game-agnostic care experience.

Session scores live in the game and its window only. This coordinator
receives their brief, immutable summary at close and never persists it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..games.rock_paper_scissors import Score
from ..pet.fun import GameExperience
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.state import PetState
from .active_time import (
    ActiveSessionClock,
    SessionInputs,
    TimeProgression,
    advance_session_time,
)


def experience_from_rock_paper_scissors(score: Score) -> GameExperience:
    """The existing RPS score is from the *player's* perspective."""
    return GameExperience(
        game_id="rock_paper_scissors",
        completed_units=score.games,
        successful_units=score.losses,  # Aiko won.
        neutral_units=score.draws,
        setback_units=score.wins,       # The player won.
    )


@dataclass(frozen=True, slots=True)
class GameExperienceOutcome:
    """Only the effect survives; no round score belongs in pet storage."""

    fun_gained: float
    fun_after: float


class GameExperienceCoordinator:
    """Owner-thread use case for completed games, independent of Tk windows."""

    def __init__(
        self, state: PetState, mind: PetMind, adaptive: AdaptiveRoutine, *,
        clock: ActiveSessionClock,
        progression: TimeProgression | None = None,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock
        self._progression = progression

    def complete(
        self, experience: GameExperience, inputs: SessionInputs,
    ) -> GameExperienceOutcome:
        """Account for elapsed awake time, then commit exactly one session."""
        if experience.completed_units == 0:
            return GameExperienceOutcome(0.0, self._state.fun)
        advance_session_time(
            self._state, self._clock, inputs, progression=self._progression,
        )
        gained = self._state.record_game_experience(
            experience, now=inputs.wall_time,
        )
        self._adaptive.note_interaction(inputs.wall_time)
        self._mind.after_care("play", inputs.monotonic_time)
        return GameExperienceOutcome(gained, self._state.fun)
