"""Desktop walk driving is separate from sprite rendering and Tk timing."""

import unittest
from dataclasses import dataclass, replace

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.desktop.walk_runtime import WalkDriver, WalkDriverPorts
from aiko_pet.pet.movement.contracts import WalkStep


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
            state=WalkNeeds(),
            settings=self.settings,
            adaptive=FocusReadings(),
            monitor=ActivityReadings(),
            walk_cycle_seconds=1.28,
            ports=WalkDriverPorts(
                track=lambda: TaskbarTrack(0, 800, 800),
                menu_engaged=lambda: False,
                place_x=place,
                walk_finished=self.finished.append,
            ),
        )

    def test_movement_runs_to_completion_without_any_canvas(self) -> None:
        self.driver.movement.remaining_distance = 12
        self.assertEqual(
            self.driver.step(100.0, 0.5, game_mode=False, attention_active=False),
            WalkStep(12, 1),
        )
        self.assertEqual(self.settings.x, 112)
        self.assertEqual(self.driver.movement.remaining_distance, 0.0)
        self.assertEqual(self.finished, [])

    def test_game_mode_does_not_advance_existing_walk(self) -> None:
        self.driver.movement.remaining_distance = -40
        self.assertIsNone(
            self.driver.step(100.0, 1.0, game_mode=True, attention_active=False),
        )
        self.assertEqual(self.settings.x, 100)
        self.assertEqual(self.driver.movement.remaining_distance, -40)

    def test_menu_use_preserves_committed_object_approach(self) -> None:
        self.driver.ports = replace(
            self.driver.ports,
            menu_engaged=lambda: True,
            committed_goal=lambda: True,
        )
        self.driver.movement.set_goal(112)
        self.assertIsNone(
            self.driver.step(100, 0.5, game_mode=False, attention_active=True),
        )
        self.assertEqual(self.settings.x, 100)
        self.assertEqual(self.driver.movement.goal_x, 112)

    def test_menu_use_still_holds_incidental_wandering(self) -> None:
        self.driver.ports = replace(self.driver.ports, menu_engaged=lambda: True)
        self.driver.movement.remaining_distance = 12
        self.assertIsNone(
            self.driver.step(100, 0.5, game_mode=False, attention_active=False),
        )
        self.assertEqual(self.settings.x, 100)

    def test_disable_auto_walk_cancels_active_motion(self) -> None:
        self.driver.movement.remaining_distance = 40
        self.driver.set_auto_walk(False, 100.0)
        self.assertFalse(self.settings.auto_walk)
        self.assertEqual(self.driver.movement.remaining_distance, 0.0)
        self.assertGreater(self.driver.movement.next_walk_at, 100.0)

    def test_escape_budget_counts_translation_only_and_completes_once(self):
        from aiko_pet.pet.mind.cursor_behaviour import CursorIntent

        for scale in (1, 2):
            with self.subTest(scale=scale):
                self.setUp()
                self.settings.scale = scale
                completed = []
                self.driver.ports = replace(
                    self.driver.ports,
                    cursor_allowed=lambda: True,
                    cursor_finished=completed.append,
                )
                self.driver.apply_cursor_intent(CursorIntent("flee", 1, 7, 1000), 10)
                # Zero elapsed selection/turning and game pause spend no budget.
                for now in (10, 20, 30):
                    self.driver.step(now, 0, game_mode=False, attention_active=True)
                self.driver.step(31, 5, game_mode=True, attention_active=False)
                before = self.settings.x
                for i in range(20):
                    self.driver.step(
                        32 + i * 0.1, 0.1, game_mode=False, attention_active=True
                    )
                distance = self.settings.x - before
                self.assertLessEqual(distance, 68 / 1.28 * scale + 0.5)
                self.assertGreater(distance, 50 * scale)
                self.assertEqual(
                    [(c.token, c.reason) for c in completed], [(7, "budget")]
                )

    def test_second_step_is_admitted_at_boundary_and_can_be_cancelled(self):
        from aiko_pet.pet.mind.cursor_behaviour import CursorIntent

        allowed = [True]
        completed = []
        self.driver.ports = replace(
            self.driver.ports,
            cursor_allowed=lambda: allowed[0],
            cursor_finished=completed.append,
        )
        self.driver.apply_cursor_intent(
            CursorIntent("approach", 1, 9, 100, steps=2), 10
        )
        self.driver.step(10, 2, game_mode=False, attention_active=True)
        self.assertEqual(self.settings.x, 116)
        allowed[0] = False
        self.driver.step(11, 2, game_mode=False, attention_active=True)
        self.driver.step(12, 2, game_mode=False, attention_active=True)
        self.assertEqual(self.settings.x, 116)
        self.assertEqual([(c.token, c.reason) for c in completed], [(9, "cancelled")])
