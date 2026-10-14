"""Translate individual minigames into one game-agnostic care experience.

Session scores live in the game and its window only. This coordinator
receives their brief, immutable summary at close and never persists it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..games.rock_paper_scissors import Score
from ..personality.adaptive import AdaptiveRoutine
from ..personality.mind import AikoMind
from ..pet.fun import GameExperience
from ..pet.state import PetState
from .active_time import ActiveSessionClock
from .controller import CareRuntime


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
        self, state: PetState, mind: AikoMind, adaptive: AdaptiveRoutine, *,
        clock: ActiveSessionClock,
    ) -> None:
        self._state = state
        self._mind = mind
        self._adaptive = adaptive
        self._clock = clock

    def complete(
        self, experience: GameExperience, runtime: CareRuntime,
    ) -> GameExperienceOutcome:
        """Account for elapsed awake time, then commit exactly one session."""
        if experience.completed_units == 0:
            return GameExperienceOutcome(0.0, self._state.fun)
        self._state.advance(
            runtime.wall_time, auto_routine=runtime.auto_routine,
            allow_bedtime=runtime.allow_bedtime,
            allow_nap=runtime.allow_nap,
            interrupt_nap=runtime.interrupt_nap,
            effort=runtime.effort,
            elapsed_seconds=self._clock.consume(),
            food_activity=runtime.food_activity,
        )
        gained = self._state.record_game_experience(
            experience, now=runtime.wall_time,
        )
        self._adaptive.note_interaction(runtime.wall_time)
        self._mind.after_care("play", runtime.monotonic_time)
        return GameExperienceOutcome(gained, self._state.fun)
