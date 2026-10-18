"""Independent hover model contracts (no desktop/Tk dependencies)."""

import unittest

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.projections import project_hover
from tools.pet_test_support import set_test_pet_values


class HoverModelTests(unittest.TestCase):
    def test_snapshot_is_disconnected_from_mutable_pet(self) -> None:
        state = PetState(affection=40)
        model = project_hover(
            snapshot_pet(state), context_at(1_781_000_000),
            ComputerSnapshot(cpu=80), observe_computer=True,
        )
        set_test_pet_values(state, affection=95)
        self.assertEqual(model.need_value("affection"), 40)
        self.assertIn("CPU 80 %", model.hardware_line)
        with self.assertRaises(KeyError):
            model.need_value("unknown")

    def test_unmonitored_model_has_no_hardware_data(self) -> None:
        model = project_hover(
            snapshot_pet(PetState()), context_at(1_781_000_000),
            ComputerSnapshot(cpu=94), observe_computer=False,
        )
        self.assertEqual(model.hardware_line, "Rechnerbeobachtung deaktiviert")
        self.assertEqual(model.workload_line, "")
        self.assertEqual(len(model.needs), 7)


if __name__ == "__main__":
    unittest.main()
