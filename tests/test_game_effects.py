"""Native setup and z-order work must not repeat inside an animation frame."""

import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from aiko_pet.ui.pet_view.game_effects import GameEffects


class GameEffectsTests(unittest.TestCase):
    def test_moving_and_reshowing_a_card_does_not_reconfigure_or_raise_each_frame(self):
        root = tk.Tk()
        self.addCleanup(root.destroy)
        root.withdraw()
        owner = tk.Toplevel(root)
        owner.withdraw()
        configure = Mock()
        effects = GameEffects(owner, topmost=False, configure=configure)
        self.addCleanup(effects.close)
        card = tk.PhotoImage(master=root, width=128, height=128)
        effects.show('card', card, 10, 20)
        window, label = effects._windows['card']
        with patch.object(window, 'deiconify') as show, \
                patch.object(label, 'configure') as paint:
            for frame in range(30):
                effects.show('card', card, 10 + frame, 20 + frame)
            show.assert_not_called()
            paint.assert_not_called()
        configure.assert_called_once_with(window)
        effects.hide('card')
        effects.show('card', card, 30, 40)
        configure.assert_called_once_with(window)
        control = Mock()
        for _ in range(10):
            effects.control('card', control, lambda: None)
        control.assert_called_once_with(window)
        effects.close()
        self.assertFalse(effects._windows)
        self.assertFalse(effects._frames)


class MastermindFinaleTests(unittest.TestCase):
    def test_snack_uses_the_supplied_hand_anchor_and_finishes_after_the_action(self):
        from aiko_pet.ui.common.mastermind_images import MastermindImages
        from aiko_pet.ui.windows.game_contracts import GameCodePorts
        from aiko_pet.ui.windows.game_presentation import GamePresentation
        from aiko_pet.ui.windows.mastermind_finale import MastermindFinale
        from tools.tk_test_time import ControlledTkTime

        with ControlledTkTime() as clock:
            try:
                root = tk.Tk()
            except tk.TclError as error:
                raise unittest.SkipTest("Native Tk display required") from error
            self.addCleanup(root.destroy)
            root.withdraw()
            owner = tk.Toplevel(root)
            owner.withdraw()
            for scale in (1, 2):
                with self.subTest(scale=scale):
                    action, done = Mock(), Mock()
                    presentation = GamePresentation(
                        action=action, cancel=Mock(), look=Mock(),
                        origin=lambda: (100, 200, scale),
                        food_anchor=lambda _clip, index: (
                            (96, 100) if index < 66 else None
                        ),
                    )
                    code = GameCodePorts(MastermindImages(root), Mock(), Mock(), Mock())
                    finale = MastermindFinale(owner, code, presentation, topmost=False)
                    try:
                        finale.play(True, done)
                        clock.advance(.5)
                        clip, duration, marker, finished = action.call_args.args
                        self.assertEqual((clip, duration), ("eat", None))
                        done.assert_not_called()
                        for index in (0, 65, 66, 84):
                            marker(index)
                            self.assertEqual(
                                "snack" in finale.effects._visible, index < 66,
                            )
                            if index < 66:
                                image, geometry = finale.effects._frames["snack"]
                                self.assertEqual(geometry,
                                    f"{image.width()}x{image.height()}"
                                    f"+{100 + 87 * scale}+{200 + 86 * scale}")
                        finished()
                        done.assert_called_once_with()
                        self.assertFalse(finale.effects._visible)
                    finally:
                        finale.close()
