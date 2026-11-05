"""Long care-day balance scenarios, separate from normal application checks."""

import unittest
from datetime import datetime

from aiko_pet.pet.state import PetState

NOW = datetime(2026, 10, 13, 10).timestamp()


class HourlyCareBalanceTests(unittest.TestCase):

    def full_state(self) -> PetState:
        return PetState(satiety=100, mood=100, energy=100, social=100,
                        affection=100, updated_at=NOW)

    def test_eight_hour_care_day_stays_playable_and_bond_is_capped(self) -> None:
        state = self.full_state()
        for hour in range(1, 9):
            stamp = NOW + hour * 3600
            state.advance(stamp, elapsed_seconds=3600)
            state.interact('feed', now=stamp)
            if hour % 3 == 0:
                state.interact('talk', now=stamp)
            if hour % 4 == 0:
                state.interact('pet', now=stamp)
                state.interact('play', now=stamp)
            self.assertGreater(min(state.satiety, state.mood, state.energy,
                                   state.social, state.affection), 20)
        self.assertLessEqual(state.friendship, 20)
