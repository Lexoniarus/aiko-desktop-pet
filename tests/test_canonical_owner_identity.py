"""One authoritative identity audit for canonical implementation owners.

Old forwarding modules have been removed. This table preserves every former
identity assertion without keeping a separate test module for each move.
"""

from __future__ import annotations

import unittest
from importlib import import_module


OWNERS = {
    "aiko_pet.pet.animation.character": (
        "AnimationClip", "CharacterCatalog",
    ),
    "aiko_pet.pet.animation.item_assets": (
        "ItemCatalog", "ItemSprite",
    ),
    "aiko_pet.ui.common.window_drag": (
        "WindowDrag", "bounded_position",
    ),
    "aiko_pet.ui.common.skin": ("AikoSkin",),
    "aiko_pet.ui.pet_view.animated_pet": ("AnimatedPet",),
    "aiko_pet.ui.pet_view.desktop_window": ("DesktopWindow",),
    "aiko_pet.ui.pet_view.speech_presenter": ("SpeechPresenter",),
    "aiko_pet.ui.pet_view.reaction_player": ("ReactionPlayer",),
    "aiko_pet.ui.pet_view.character_sprite_cache": ("CharacterSpriteCache",),
    "aiko_pet.ui.pet_view.food_overlay": ("FoodOverlay",),
    "aiko_pet.ui.pet_view.rest_pose_renderer": ("RestPoseRenderer",),
    "aiko_pet.ui.windows.action_toolbar": ("ActionToolbar",),
    "aiko_pet.ui.windows.food_menu": ("FoodMenu",),
    "aiko_pet.ui.windows.settings_window": ("SettingsWindow",),
    "aiko_pet.ui.windows.hover_ui": ("HoverUi",),
    "aiko_pet.ui.windows.hover_geometry": ("HoverGeometry",),
    "aiko_pet.ui.windows.toolbar_details": ("ToolbarDetails",),
    "aiko_pet.ui.windows.rock_paper_scissors_sequence": (
        "RockPaperScissorsSequence",
    ),
    "aiko_pet.ui.windows.rock_paper_scissors_window": (
        "RockPaperScissorsWindow",
    ),
    "aiko_pet.ui.view_models.contracts": ("StatusSnapshot",),
    "aiko_pet.ui.view_models.food_models": ("FoodChoice",),
    "aiko_pet.ui.view_models.read_models": ("DesktopPresentation",),
    "aiko_pet.ui.view_models.projections": ("project_hover",),
}


class CanonicalOwnerIdentityTests(unittest.TestCase):
    def test_symbols_are_defined_by_exactly_their_named_owner(self) -> None:
        for module_name, names in OWNERS.items():
            module = import_module(module_name)
            for name in names:
                with self.subTest(owner=module_name, name=name):
                    symbol = getattr(module, name)
                    self.assertEqual(symbol.__module__, module_name)


if __name__ == "__main__":
    unittest.main()
