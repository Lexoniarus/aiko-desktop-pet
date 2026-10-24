"""Typed any/excluded wishes remain readable and renderable without native Tk."""

import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock, patch

from test_wish_assignment import wish

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import WishId, WishState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.common.description_tip import DescriptionTip
from aiko_pet.ui.common.icon_images import IconImages
from aiko_pet.ui.view_models.emotional_text import wish_description, wish_icon
from aiko_pet.ui.view_models.food_models import food_choices
from aiko_pet.ui.view_models.projections import project_hover, project_status
from aiko_pet.ui.windows.wish_panel import WishPanel
from tools.headless_widgets import Skin, Widget, widgets


class FlexibleWishReadTests(unittest.TestCase):
    def test_free_choice_and_exclusion_preserve_their_meaning_in_both_views(self):
        for key, target, expected, icon in (
            (WishId.PLAY_ANY_GAME, None, "Spiel frei wählen", "status_fun"),
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

    def test_every_current_target_builds_with_the_packaged_icon_catalog(self):
        food_icons = {choice.id: choice.image_path
                      for choice in food_choices(load_item_catalog())}
        for key, definition in WISH_CATALOG.definitions.items():
            targets = (None,) if definition.target_mode == "any" else definition.targets
            for target in targets:
                with self.subTest(key=key, target=target), widgets():
                    pet = PetState(wishes=WishState(2, (wish(key, target),)))
                    views = project_hover(
                        snapshot_pet(pet), context_at(1800000000),
                        ComputerSnapshot(), observe_computer=False,
                    ).emotional.wishes
                    root, skin = Widget(), Skin()
                    icons = IconImages(cast(Any, Mock()))

                    def file(path, _size):
                        self.assertTrue(path.is_file(), str(path))
                        return object()

                    with (
                        patch("aiko_pet.ui.common.icon_images.tk.PhotoImage"),
                        patch.object(skin.images, "icon", icons.icon),
                        patch.object(skin.images, "file", file),
                    ):
                        panel = WishPanel(
                            cast(Any, root), cast(Any, skin),
                            DescriptionTip(cast(Any, root), cast(Any, skin)),
                            food_icons,
                        )
                        panel.refresh(views)
                    self.assertTrue(panel._labels[1].cget("text").strip())
                    self.assertTrue(panel._meta[1].cget("text").strip())

    def test_interrupted_card_build_is_rebuilt_for_the_same_wish_identity(self):
        pet = PetState(wishes=WishState(2, (wish(WishId.PLAY_ANY_GAME, None),)))
        views = project_hover(
            snapshot_pet(pet), context_at(1800000000), ComputerSnapshot(),
            observe_computer=False,
        ).emotional.wishes
        with widgets():
            root, skin = Widget(), Skin()
            panel = WishPanel(
                cast(Any, root), cast(Any, skin),
                DescriptionTip(cast(Any, root), cast(Any, skin)), {},
            )
            with patch.object(skin.images, "icon", side_effect=KeyError("missing")):
                with self.assertRaises(KeyError):
                    panel.refresh(views)
            self.assertIsNone(panel._ids)
            panel.refresh(views)
            self.assertEqual(len(panel._scroll.body.winfo_children()), 1)
            self.assertEqual(panel._labels[1].cget("text"), "Spiel frei wählen")


if __name__ == "__main__":
    unittest.main()
