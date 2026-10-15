"""Windows button state is polled without global keyboard monitoring."""

import unittest

from aiko_pet.desktop.global_input import VK_LBUTTON, VK_RBUTTON, GlobalMouseClicks


class GlobalClickTests(unittest.TestCase):
    def test_initial_held_click_does_not_close_popups_immediately(self):
        states = {VK_LBUTTON: 0x8000, VK_RBUTTON: 0}
        observer = GlobalMouseClicks(lambda key: states[key])
        self.assertFalse(observer.clicked())
        self.assertFalse(observer.clicked())
        states[VK_LBUTTON] = 0
        self.assertFalse(observer.clicked())
        states[VK_LBUTTON] = 0x8001
        self.assertTrue(observer.clicked())
        states[VK_LBUTTON] = 0x8000
        self.assertFalse(observer.clicked())

    def test_short_click_uses_low_bit_and_right_button_also_works(self):
        states = {VK_LBUTTON: 0, VK_RBUTTON: 0}
        observer = GlobalMouseClicks(lambda key: states[key])
        self.assertFalse(observer.clicked())
        states[VK_LBUTTON] = 1
        self.assertTrue(observer.clicked())
        states[VK_LBUTTON] = 0
        self.assertFalse(observer.clicked())
        states[VK_RBUTTON] = 0x8001
        self.assertTrue(observer.clicked())


if __name__ == "__main__":
    unittest.main()
