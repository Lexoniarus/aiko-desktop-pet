"""Independent hover model contracts (no desktop/Tk dependencies)."""

import unittest
from unittest.mock import MagicMock

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.projections import project_hover
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.hover_contracts import HoverActions
from tools.pet_test_support import set_test_pet_values


class HoverModelTests(unittest.TestCase):
    def test_toolbar_formats_all_status_readouts_without_treating_them_as_needs(self):
        view = project_hover(
            snapshot_pet(PetState(mood=33, friendship=71)),
            context_at(1_781_000_000), ComputerSnapshot(), observe_computer=False,
        )
        toolbar = ActionToolbar.__new__(ActionToolbar)
        toolbar._snapshot = lambda: view
        toolbar._actions = MagicMock(spec=HoverActions)
        toolbar.buttons = MagicMock()
        toolbar.today = MagicMock()
        toolbar.hardware = MagicMock()
        toolbar.workload = MagicMock()
        toolbar.food_info = MagicMock()
        toolbar.visible = False
        toolbar.details = None
        toolbar._details_open = False
        toolbar.readouts = {}
        labels = {}
        for key, _title, _color in toolbar.READOUTS:
            bar, label = MagicMock(), MagicMock()
            bar.winfo_width.return_value = 92
            bar.winfo_reqheight.return_value = 10
            toolbar.readouts[key] = (bar, 1, label)
            labels[key] = label
        toolbar.refresh()
        self.assertEqual(len(toolbar.readouts), 7)
        self.assertIn("33%", labels["mood"].configure.call_args.kwargs["text"])
        self.assertIn("Lv 8", labels["friendship"].configure.call_args.kwargs["text"])

    def test_snapshot_is_disconnected_from_mutable_pet(self) -> None:
        state = PetState(affection=40)
        model = project_hover(
            snapshot_pet(state), context_at(1_781_000_000),
            ComputerSnapshot(cpu=80), observe_computer=True,
        )
        set_test_pet_values(state, affection=95)
        self.assertEqual(model.status_value("affection"), 40)
        self.assertIn("CPU 80 %", model.hardware_line)
        with self.assertRaises(KeyError):
            model.status_value("unknown")

    def test_unmonitored_model_has_no_hardware_data(self) -> None:
        model = project_hover(
            snapshot_pet(PetState()), context_at(1_781_000_000),
            ComputerSnapshot(cpu=94), observe_computer=False,
        )
        self.assertEqual(model.hardware_line, "Rechnerbeobachtung deaktiviert")
        self.assertEqual(model.workload_line, "")
        self.assertEqual(len(model.status_values), 7)


if __name__ == "__main__":
    unittest.main()
