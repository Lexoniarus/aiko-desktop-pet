"""Typed any/excluded wishes remain readable and renderable without native Tk."""

import unittest
from pathlib import Path
from typing import Any, cast

from test_wish_assignment import wish

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import WishId, WishState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.common.description_tip import DescriptionTip
from aiko_pet.ui.view_models.emotional_text import wish_description, wish_icon
from aiko_pet.ui.view_models.projections import project_hover, project_status
from aiko_pet.ui.windows.wish_panel import WishPanel
from tools.headless_widgets import Skin, Widget, widgets


class FlexibleWishReadTests(unittest.TestCase):
    def test_free_choice_and_exclusion_preserve_their_meaning_in_both_views(self):
        for key, target, expected, icon in (
            (WishId.PLAY_ANY_GAME, None, "Spiel frei wählen", "action_play"),
            (WishId.SOCIAL_ANY, None, "Unterhaltung frei wählen", "status_social"),
            (
                WishId.PLAY_OTHER_GAME,
                "mastermind",
                "Etwas anderes als Mastermind",
                "mastermind",
            ),
            (WishId.AVOID_FOOD, "apple", "Etwas anderes als Apfel", "food"),
        ):
            with self.subTest(key=key):
                desired = wish(key, target)
                pet = PetState(wishes=WishState(2, (desired,)))
                before = pet.capture_checkpoint()
                read = snapshot_pet(pet)
                hover = project_hover(
                    read,
                    context_at(1800000000),
                    ComputerSnapshot(),
                    observe_computer=False,
                )
                status = project_status(
                    read,
                    context_at(1800000000),
                    None,
                    ComputerSnapshot(),
                    observe_computer=False,
                )
                self.assertEqual(hover.emotional, status.emotional)
                view = hover.emotional.wishes[0]
                self.assertEqual(view.target_label, expected)
                self.assertIn(expected, wish_description(view))
                self.assertEqual(wish_icon(view), icon)
                self.assertEqual(read.wishes[0].target, desired.target)
                with widgets():
                    root, skin = Widget(), Skin()
                    tips = DescriptionTip(cast(Any, root), cast(Any, skin))
                    panel = WishPanel(cast(Any, root), cast(Any, skin), tips,
                                      {'apple': Path('apple.png')})
                    panel.refresh((view,))
                    self.assertEqual(panel._ids, (desired.instance_id,))
                self.assertEqual(pet.capture_checkpoint(), before)


if __name__ == "__main__":
    unittest.main()
