"""The 4K transform is shared, stable before mapping and preserves native input."""

import tkinter as tk
import unittest

from aiko_pet.ui.common import scaled_widgets as scaled
from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.common.ui_scale import DisplayScale, UiScale
from tools.desktop_test_support import destroy_test_root


class DisplayScaleTests(unittest.TestCase):
    def test_resolution_ratios_and_aspect_ratios_use_one_factor(self):
        for size, expected in (
            ((3840, 2160), 1), ((2560, 1440), 2 / 3),
            ((1920, 1080), .5), ((3440, 1440), 2 / 3),
            ((7680, 4320), 1),
        ):
            with self.subTest(size=size):
                transform = DisplayScale.for_resolution(*size)
                self.assertEqual(transform.factor, expected)
                self.assertAlmostEqual(transform.logical(120 * expected), 120)
        for size in ((0, 1080), (1920, -1)):
            with self.assertRaises(ValueError):
                DisplayScale.for_resolution(*size)


class NativeUiScaleTests(unittest.TestCase):
    def test_status_actions_have_full_bounds_at_4k_and_full_hd(self):
        from unittest.mock import Mock

        from aiko_pet.application.read_snapshot import snapshot_pet
        from aiko_pet.pet.routine import context_at
        from aiko_pet.pet.state import PetState
        from aiko_pet.telemetry import ComputerSnapshot
        from aiko_pet.ui.view_models.contracts import HoverAnchor
        from aiko_pet.ui.view_models.projections import project_hover
        from aiko_pet.ui.windows.action_toolbar import ActionToolbar
        from aiko_pet.ui.windows.hover_contracts import HoverActions

        view = project_hover(snapshot_pet(PetState()), context_at(1_800_000_000),
                             ComputerSnapshot(), observe_computer=False)
        for size in ((3840, 2160), (1920, 1080)):
            with self.subTest(size=size):
                root = tk.Tk()
                root.withdraw()
                try:
                    transform = UiScale(root, DisplayScale.for_resolution(*size))
                    UiScale._roots[root] = transform
                    skin = AikoSkin(root)
                    calls = []
                    menu = ActionToolbar(
                        root, snapshot=lambda: view,
                        anchor=lambda: HoverAnchor(100, 100, 192, 208, None, None),
                        actions=HoverActions(calls.append, Mock(), Mock(), Mock(),
                                             Mock(), lambda: True),
                        always_on_top=False, skin=skin,
                    )
                    menu.show()
                    root.update()
                    for action, button in menu.buttons.items():
                        self.assertIs(button.ui_scale, transform)
                        self.assertGreaterEqual(button.winfo_width(),
                                                button.winfo_reqwidth())
                        self.assertGreaterEqual(button.winfo_height(),
                                                button.winfo_reqheight())
                        menu.tips.hide()
                        calls.clear()
                        for event in (
                            '<Enter>', '<ButtonPress-1>', '<ButtonRelease-1>',
                        ):
                            button.event_generate(event, x=button.winfo_width() // 2,
                                                  y=button.winfo_height() // 2)
                        root.update()
                        self.assertEqual(calls, [action])
                    menu.close()
                finally:
                    root.destroy()

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(destroy_test_root, self.root)
        # One application-wide startup policy, independent of individual forms.
        self.scale = UiScale(self.root, DisplayScale.for_resolution(1920, 1080))
        UiScale._roots[self.root] = self.scale
        self.skin = AikoSkin(self.root)

    def test_all_skins_and_nested_views_share_the_same_transform(self):
        other = AikoSkin(self.root)
        windows = [tk.Toplevel(self.root) for _ in range(2)]
        for window in windows:
            window.withdraw()
            frame = scaled.Frame(window, width=600, height=800)
            canvas = scaled.Canvas(frame, width=460, height=504)
            button = other.button(frame, 'Test', lambda: None)
            for widget in (frame, canvas, button):
                self.assertIs(widget.ui_scale, self.scale)
            self.assertEqual(int(canvas.cget('width')), 230)
            self.assertEqual(int(canvas.cget('height')), 252)
        self.assertIs(other.scale, self.skin.scale)

    def test_animation_updates_and_images_are_scaled_before_first_mapping(self):
        canvas = scaled.Canvas(self.root, width=400, height=200)
        canvas.pack()
        source = tk.PhotoImage(master=self.root, width=80, height=40)
        source.put('white', to=(0, 0, 40, 40))
        source.put('black', to=(40, 0, 80, 40))
        item = canvas.create_image(100, 50, image=source)
        self.assertEqual(canvas.tk.call(str(canvas), 'coords', item), (50.0, 25.0))
        name = canvas.itemcget(item, 'image')
        self.assertEqual(int(canvas.tk.call('image', 'width', name)), 40)
        # Filtered scaling has intermediate edge colors, rather than nearest
        # neighbour's blocky, all-black/all-white edge.
        edge = self.root.tk.call(name, 'get', 19, 10)
        self.assertTrue(0 < edge[0] < 255)
        canvas.coords(item, 200, 100)
        self.assertEqual(canvas.tk.call(str(canvas), 'coords', item), (100.0, 50.0))
        canvas.delete(item)
        new = canvas.create_rectangle(20, 40, 120, 140)
        self.assertEqual(canvas.tk.call(str(canvas), 'coords', new),
                         (10.0, 20.0, 60.0, 70.0))
        self.assertEqual(self.root.state(), 'withdrawn')

    def test_native_button_remains_clickable_and_layout_never_reverts_to_4k(self):
        window = tk.Toplevel(self.root)
        window.withdraw()
        frame = scaled.Frame(window, width=600, height=400)
        frame.pack_propagate(False)
        frame.pack()
        clicked = []
        button = self.skin.button(frame, 'Test', lambda: clicked.append(True))
        button.pack(padx=20, pady=20)
        window.update_idletasks()
        self.assertEqual((frame.winfo_reqwidth(), frame.winfo_reqheight()), (300, 200))
        window.deiconify()
        for _ in range(4):
            window.update()
            self.assertEqual((frame.winfo_width(), frame.winfo_height()), (300, 200))
        for event in ('<Enter>', '<ButtonPress-1>', '<ButtonRelease-1>'):
            button.event_generate(event, x=button.winfo_width() // 2,
                                  y=button.winfo_height() // 2)
        window.update()
        self.assertEqual(clicked, [True])

    def test_pixel_fonts_ignore_changes_to_global_tk_dpi(self):
        label = scaled.Label(self.root, text='Aiko', font=('Arial', 12))
        first = self.root.tk.call('font', 'actual', label.cget('font'), '-size')
        original = self.root.tk.call('tk', 'scaling')
        self.addCleanup(lambda: self.root.tk.call('tk', 'scaling', original))
        self.root.tk.call('tk', 'scaling', 2)
        second = scaled.Label(self.root, text='Aiko', font=('Arial', 12))
        self.assertEqual(
            self.root.tk.call('font', 'actual', second.cget('font'), '-size'), first,
        )
