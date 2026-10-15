"""Desktop walk driving is separate from sprite rendering and Tk timing."""

import unittest
from dataclasses import dataclass

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.desktop.walk_runtime import WalkDriver, WalkDriverPorts


@dataclass
class WalkSettings:
    x: int | None = 100
    scale: int = 1
    auto_walk: bool = True
    observe_computer: bool = False


@dataclass
class WalkNeeds:
    energy: float = 80.0
    sleeping: bool = False


class FocusReadings:
    current = None


class BusyState:
    def is_busy(self) -> bool:
        return False


class ActivityReadings:
    def latest(self) -> BusyState:
        return BusyState()


class WalkDriverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = WalkSettings()
        self.finished: list[float] = []

        def place(x: float) -> None:
            self.settings.x = round(x)

        self.driver = WalkDriver(
            state=WalkNeeds(), settings=self.settings,
            adaptive=FocusReadings(), monitor=ActivityReadings(),
            walk_cycle_seconds=1.28,
            ports=WalkDriverPorts(
                track=lambda: TaskbarTrack(0, 800, 800),
                toolbar_visible=lambda: False,
                place_x=place,
                walk_finished=self.finished.append,
            ),
        )

    def test_movement_runs_to_completion_without_any_canvas(self) -> None:
        self.driver.movement.remaining_distance = 12
        self.assertEqual(
            self.driver.step(100.0, 0.5, game_mode=False,
                             attention_active=False),
            "running-right",
        )
        self.assertEqual(self.settings.x, 112)
        self.assertEqual(self.driver.movement.remaining_distance, 0.0)
        self.assertEqual(self.finished, [100.0])

    def test_game_mode_does_not_advance_existing_walk(self) -> None:
        self.driver.movement.remaining_distance = -40
        self.assertIsNone(
            self.driver.step(100.0, 1.0, game_mode=True,
                             attention_active=False),
        )
        self.assertEqual(self.settings.x, 100)
        self.assertEqual(self.driver.movement.remaining_distance, -40)

    def test_disable_auto_walk_cancels_active_motion(self) -> None:
        self.driver.movement.remaining_distance = 40
        self.driver.set_auto_walk(False, 100.0)
        self.assertFalse(self.settings.auto_walk)
        self.assertEqual(self.driver.movement.remaining_distance, 0.0)
        self.assertGreater(self.driver.movement.next_walk_at, 100.0)
