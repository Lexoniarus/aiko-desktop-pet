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
