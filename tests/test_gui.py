"""Functional GUI smoke tests (automatically skipped without a display)."""

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import tkinter as tk
from types import SimpleNamespace

from aiko_pet.gui import DesktopPet
from aiko_pet.storage import StateStore


class TaskbarPetGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"No working graphical display: {error}") from error
        probe.withdraw()
        probe.destroy()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.app = DesktopPet(store=StateStore(Path(self.folder.name) / "state.json"))
        self.addCleanup(self.app.quit)
        self.app.root.update_idletasks()
        # GUI tests must not depend on whether the test runner's local time
        # happens to be Aiko's bedtime.
        self.app.settings.auto_routine = False
        self.app.state.sleeping = False

    def test_hover_toolbar_contains_every_care_action(self):
        self.app._on_enter()
        self.assertIsNotNone(self.app.toolbar)
        bar = self.app.toolbar
        self.assertTrue(bar.visible)
        self.assertEqual(set(bar.buttons), {"feed", "play", "pet", "sleep",
                                             "talk", "energy_drink"})
        action_row = bar.buttons["feed"].master
        labels = [
            child.cget("text") for child in action_row.winfo_children()
            if "text" in child.keys()
        ]
        self.assertIn("Reden", labels)
        extra_row = bar.buttons["sleep"].master
        extra_labels = [
            child.cget("text") for child in extra_row.winfo_children()
            if "text" in child.keys()
        ]
        self.assertIn("Status", extra_labels)
        bar.buttons["feed"].invoke()
        self.assertGreater(self.app.state.satiety, 75)
        bar.buttons["sleep"].invoke()
        self.assertTrue(self.app.state.sleeping)
        self.assertEqual(bar.buttons["sleep"].cget("text"), "Wecken")
        bar.buttons["sleep"].invoke()
        self.assertFalse(self.app.state.sleeping)

    def test_needs_are_visible_and_updated_in_hover_without_status_popup(self):
        self.app._on_enter()
        bar = self.app.toolbar
        self.assertIsNone(self.app.status_panel)
        self.assertEqual(set(bar.needs), {"satiety", "mood", "energy",
                                           "social", "affection", "friendship"})
        for key, _title, _color in bar.NEEDS:
            canvas, rect, label = bar.needs[key]
            self.assertIn("%", label.cget("text"))
            self.assertGreater(canvas.coords(rect)[2], 0)
        self.app.state.mood = 22
        self.app.state.satiety = 36
        self.app.state.energy = 95
        bar.refresh()
        self.assertIn("22%", bar.needs["mood"][2].cget("text"))
        self.assertIn("36%", bar.needs["satiety"][2].cget("text"))
        self.assertIn("95%", bar.needs["energy"][2].cget("text"))
        self.app.root.update()
        self.assertEqual(bar.needs["mood"][0].coords(
            bar.needs["mood"][1])[2], round(max(
                bar.needs["mood"][0].winfo_width(),
                bar.needs["mood"][0].winfo_reqwidth(),
            ) * .22))

    def test_busy_computer_makes_aiko_concentrate_instead_of_walking(self):
        from aiko_pet.system_activity import ComputerSnapshot
        self.app.center()
        original_x = self.app.settings.x
        self.app._walk_remaining = 300
        with patch.object(self.app.activity_monitor, "latest", return_value=
                          ComputerSnapshot(cpu=94, ram=67)):
            self.assertIsNone(self.app._maybe_walk(time.monotonic(), .2))
            self.assertEqual(self.app._walk_remaining, 0)
            self.assertEqual(original_x, self.app.settings.x)
        self.assertFalse(self.app.state.sleeping)

    def test_disable_hardware_observation_keeps_needs_visible(self):
        self.app._on_enter()
        self.app.set_observe_computer(False)
        self.assertFalse(self.app.settings.observe_computer)
        self.assertIn("deaktiviert", self.app.toolbar.hardware.cget("text"))
        self.assertIn("Sättigung", self.app.toolbar.needs["satiety"][2].cget("text"))
        self.app.set_observe_computer(True)
        self.assertTrue(self.app.settings.observe_computer)
        self.assertIn("CPU", self.app.toolbar.hardware.cget("text"))

    def test_popup_can_open_toggle_and_close_repeatedly(self):
        self.app._on_enter()
        bar = self.app.toolbar
        bar.settings_button.invoke()
        self.app.root.update_idletasks()
        self.assertTrue(self.app._menu_is_open)
        self.assertIsNotNone(self.app.settings_popup)
        self.assertTrue(self.app.settings_popup.window.winfo_ismapped())
        popup = self.app.settings_popup
        self.assertTrue(bar.visible)
        # The popup is an actual set of live controls, not a dead native menu.
        popup.values["auto_walk"].set(False)
        for widget in popup.window.winfo_children()[0].winfo_children():
            if isinstance(widget, tk.Checkbutton) and widget.cget("text") == "An der Taskleiste laufen":
                widget.invoke()  # flips the variable to True again
                break
        self.assertTrue(self.app.settings.auto_walk)
        popup.close()
        self.assertFalse(self.app._menu_is_open)
        bar.settings_button.invoke()
        self.assertIsNotNone(self.app.settings_popup)
        bar.settings_button.invoke()
        self.assertIsNone(self.app.settings_popup)
        self.assertFalse(self.app._menu_is_open)

    def test_click_outside_closes_toolbar_and_settings_immediately(self):
        self.app._on_enter()
        self.app.toolbar.settings_button.invoke()
        self.assertIsNotNone(self.app.settings_popup)
        with (
            patch.object(self.app._mouse_clicks, "clicked", return_value=True),
            patch.object(self.app.root, "winfo_pointerx", return_value=-999),
            patch.object(self.app.root, "winfo_pointery", return_value=-999),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._poll_desktop_click()
        self.assertIsNone(self.app.settings_popup)
        self.assertFalse(self.app._menu_is_open)
        self.assertFalse(self.app.toolbar.visible)
        self.app._on_enter()
        self.assertTrue(self.app.toolbar.visible)
        with (
            patch.object(self.app._mouse_clicks, "clicked", return_value=True),
            patch.object(self.app.root, "winfo_pointerx", return_value=-999),
            patch.object(self.app.root, "winfo_pointery", return_value=-999),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._poll_desktop_click()
        self.assertFalse(self.app.toolbar.visible)

    def test_all_100_percent_need_bars_fill_real_display_width(self):
        self.app.state.satiety = 100
        self.app.state.mood = 100
        self.app.state.energy = 100
        self.app.state.social = 100
        self.app.state.affection = 100
        self.app.state.friendship = 100
        self.app._on_enter()
        self.app.root.update_idletasks()
        self.app.toolbar.refresh()
        for key, _title, _color in self.app.toolbar.NEEDS:
            bar, rect, text = self.app.toolbar.needs[key]
            self.assertEqual(bar.coords(rect)[2], bar.winfo_width(), key)
            self.assertIn("100%", text.cget("text"))
        self.app.state.mood = 25
        self.app.toolbar.refresh()
        bar, rect, _text = self.app.toolbar.needs["mood"]
        self.assertEqual(bar.coords(rect)[2], round(bar.winfo_width() * .25))

    def test_side_by_side_bridge_keeps_hover_active(self):
        self.app._on_enter()
        bar = self.app.toolbar
        bar.window.update_idletasks()
        pet_x, pet_y = self.app.root.winfo_rootx(), self.app.root.winfo_rooty()
        panel_x, panel_y = bar.window.winfo_rootx(), bar.window.winfo_rooty()
        width = bar.window.winfo_width()
        if panel_x >= pet_x + self.app.width:
            x = (pet_x + self.app.width + panel_x) // 2
        else:
            x = (panel_x + width + pet_x) // 2
        y = max(pet_y, panel_y) + 12
        self.assertTrue(bar.contains_bridge(x, y))
        self.app._last_hover = time.monotonic() - 10
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=x),
            patch.object(self.app.root, "winfo_pointery", return_value=y),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._refresh_hover(time.monotonic())
        self.assertTrue(bar.visible)

    def test_bubble_follows_aiko_and_never_toolbar(self):
        self.app._on_enter()
        self.app.say("...Ich schaue zu. Ist das ein Problem?", 6000)
        self.app.root.update_idletasks()
        bubble = self.app._bubble
        bubble_y = bubble.winfo_rooty()
        self.assertLess(bubble_y + bubble.winfo_height(), self.app.settings.y)
        self.app.toolbar.window.geometry("+5+5")
        self.app.toolbar._last_placement = None
        self.app._move_bubble()
        self.app.root.update_idletasks()
        self.assertEqual(bubble.winfo_rooty(), bubble_y)
        self.app._place_x(self.app.settings.x - 110)
        self.app.root.update_idletasks()
        self.assertAlmostEqual(
            bubble.winfo_rootx() + bubble.winfo_width() / 2,
            self.app.settings.x + self.app.width / 2, delta=3,
        )

    def test_drag_toolbar_save_reopen_and_reset_to_aiko(self):
        self.app._on_enter()
        bar = self.app.toolbar
        original = (bar.window.winfo_rootx(), bar.window.winfo_rooty())
        start = SimpleNamespace(x_root=original[0]+20, y_root=original[1]+20)
        bar._drag_start(start)
        self.assertTrue(bar._dragging)
        # Even a click outside while actively dragging must not dismiss it.
        self.app._dismiss_if_outside(-999, -999)
        self.assertTrue(bar.visible)
        bar._drag_motion(SimpleNamespace(
            x_root=start.x_root + 25, y_root=start.y_root - 15,
        ))
        bar.window.update_idletasks()
        bar._drag_end(start)
        self.assertFalse(bar._dragging)
        position = (self.app.settings.toolbar_x, self.app.settings.toolbar_y)
        self.assertNotEqual(position, original)
        bar.hide()
        bar.show()
        self.app.root.update_idletasks()
        self.assertEqual(
            (bar.window.winfo_rootx(), bar.window.winfo_rooty()), position,
        )
        _saved, settings = self.app.store.load(now=time.time())
        self.assertEqual((settings.toolbar_x, settings.toolbar_y), position)
        self.app.reset_toolbar_position()
        self.app.root.update()
        self.assertIsNone(self.app.settings.toolbar_x)
        self.assertIsNone(self.app.settings.toolbar_y)
        self.assertNotEqual(bar.window.winfo_rootx(), position[0])

    def test_dragged_toolbar_hides_and_reopens_at_saved_coordinates(self):
        self.app._on_enter()
        self.app.settings.toolbar_x = 25
        self.app.settings.toolbar_y = 35
        self.app.toolbar.place()
        self.app._last_hover = time.monotonic() - 10
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=-999),
            patch.object(self.app.root, "winfo_pointery", return_value=-999),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._refresh_hover(time.monotonic())
        self.assertFalse(self.app.toolbar.visible)
        self.app._on_enter()
        self.app.root.update()
        self.assertEqual(self.app.toolbar.window.winfo_rootx(), 25)
        self.assertEqual(self.app.toolbar.window.winfo_rooty(), 35)

    def test_computer_load_can_trigger_first_person_speech(self):
        from aiko_pet.system_activity import ComputerSnapshot
        self.app._on_enter()
        self.assertIn("CPU", self.app.toolbar.hardware.cget("text"))
        self.assertIn("GPU", self.app.toolbar.hardware.cget("text"))
        self.assertIn("RAM", self.app.toolbar.hardware.cget("text"))
        now = time.monotonic()
        self.app._next_comment = now - 1
        self.app._last_spoken = -9999999
        self.app.toolbar.hide()
        self.app.settings.spontaneous_talk = True
        with (
            patch.object(self.app.activity_monitor, "latest", return_value=
                         ComputerSnapshot(cpu=92, gpu=15, ram=55,
                                          measured_at=now)),
            patch.object(self.app.computer_voice, "maybe_event",
                         return_value="computer_effort_steady"),
        ):
            self.app._tick()
        self.assertTrue(self.app.mind.book.recent[-1].startswith("computer_effort_steady-"))

    def test_load_change_updates_visible_voice_and_reaction_with_hover_open(self):
        from aiko_pet.system_activity import ComputerSnapshot
        self.app._on_enter()
        self.app._last_spoken = -1000
        base = time.monotonic()
        first = ComputerSnapshot(cpu=8, gpu=5, ram=40, measured_at=base)
        second = ComputerSnapshot(cpu=89, gpu=5, ram=40, measured_at=base + 7)
        with patch.object(self.app.activity_monitor, "latest", return_value=first):
            self.app._react_to_computer(base)
            self.app.toolbar.refresh()
            self.assertIn("Ruhe", self.app.toolbar.workload.cget("text"))
        with patch.object(self.app.activity_monitor, "latest", return_value=second):
            self.app._react_to_computer(base + 7)
            self.app.toolbar.refresh()
            self.assertIn("zu tun", self.app.toolbar.workload.cget("text"))
            self.assertIsNotNone(self.app._pending_computer_line)
            self.app._react_to_computer(base + 10)
        self.assertTrue(self.app.toolbar.visible)
        self.assertIsNone(self.app._pending_computer_line)
        self.assertTrue(self.app.mind.book.recent[-1].startswith("computer_effort_rising-"))
        self.assertIsNotNone(self.app._bubble)

    def test_character_cannot_be_dragged_and_is_always_grounded(self):
        self.assertFalse(self.app.canvas.bind("<B1-Motion>"))
        self.assertEqual(
            self.app.settings.y, self.app.track.sprite_y(self.app.settings.scale),
        )
        y = self.app.settings.y
        self.app._place_x(-400)
        self.assertEqual(self.app.settings.x, self.app.track.left)
        self.app._place_x(99999)
        self.assertEqual(self.app.settings.x, self.app.track.right - self.app.width)
        self.assertEqual(self.app.settings.y, y)

    def test_walk_is_horizontal_and_stops_on_hover(self):
        self.app.center()
        original_y = self.app.settings.y
        original_x = self.app.settings.x
        self.app._walk_remaining = 140
        state = self.app._maybe_walk(time.monotonic(), .15)
        self.assertEqual(state, "running-right")
        self.assertGreater(self.app.settings.x, original_x)
        self.assertEqual(self.app.settings.y, original_y)
        self.app._on_enter()
        self.assertIsNone(self.app._maybe_walk(time.monotonic(), .15))
        self.assertEqual(self.app._walk_remaining, 0)

    def test_toolbar_auto_hides_only_when_pointer_has_left(self):
        self.app._on_enter()
        self.app._last_hover = time.monotonic() - 10
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=-999),
            patch.object(self.app.root, "winfo_pointery", return_value=-999),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._refresh_hover(time.monotonic())
        self.assertFalse(self.app.toolbar.visible)

    def test_far_away_desktop_cursor_still_gets_a_gaze_frame(self):
        self.assertEqual(self.app._gaze_direction((99999, -99999)), 2)
        self.assertIn(self.app._gaze_direction((-99999, -99999)), (14, 15))
        self.app.set_follow_cursor(False)
        self.assertIsNone(self.app._gaze_direction((99999, -99999)))

    def test_hover_bar_has_clock_and_meal_aware_button(self):
        from datetime import datetime
        from aiko_pet.routine import context_at

        morning = datetime(2026, 10, 12, 8, 20).astimezone().timestamp()
        self.app.context = context_at(morning)
        self.app.state.meals_date = ""
        self.app._on_enter()
        self.assertIn("Montag", self.app.toolbar.today.cget("text"))
        self.assertEqual(self.app.toolbar.buttons["feed"].cget("text"), "Frühstück")
        self.app.state.interact("feed", now=morning)
        self.app.toolbar.refresh()
        self.assertEqual(self.app.toolbar.buttons["feed"].cget("text"), "Snack")

    def test_startup_geometry_is_explicitly_applied_before_first_frame(self):
        # Covers the original flash at (0,0) and saved coordinates which
        # already happen to match the taskbar's calculated start position.
        self.assertTrue(self.app._placed)
        self.assertEqual(self.app.root.state(), "normal")
        self.assertEqual(self.app.root.winfo_x(), self.app.settings.x)
        self.assertEqual(self.app.root.winfo_y(), self.app.settings.y)
        self.app._placed = False
        self.app.root.geometry("128x208+0+0")
        self.app._place_x(self.app.settings.x)
        self.app.root.update_idletasks()
        self.assertEqual(self.app.root.winfo_x(), self.app.settings.x)
        self.assertEqual(self.app.root.winfo_y(), self.app.settings.y)

    def test_left_and_right_click_open_voice_reactions(self):
        self.assertIn("_on_click_left", str(self.app.canvas.bind("<Button-1>")))
        self.assertIn("_on_click_right", str(self.app.canvas.bind("<Button-3>")))
        self.app._on_click_left()
        self.assertIsNotNone(self.app._bubble)
        self.assertEqual(
            next(line.event for line in self.app.mind.book.lines
                 if line.id == self.app.mind.book.recent[-1]), "click_left",
        )
        self.app._on_click_right()
        self.assertIsNotNone(self.app._bubble)
        self.assertEqual(
            next(line.event for line in self.app.mind.book.lines
                 if line.id == self.app.mind.book.recent[-1]), "click_right",
        )
        self.assertTrue(self.app.toolbar.visible)

    def test_speech_bubble_includes_a_pixel_tail(self):
        self.app.say("...Ich habe dich bemerkt.", 6000)
        bubble = self.app._bubble
        self.assertIsNotNone(bubble)
        self.assertEqual(len(bubble.winfo_children()), 2)
        self.assertIsInstance(bubble.winfo_children()[-1], tk.Canvas)
        self.assertEqual(len(bubble.winfo_children()[-1].find_all()), 1)
        self.app._hide_bubble()
        self.assertIsNone(self.app._bubble)

    def test_chatter_switch_suppresses_autonomous_lines(self):
        from unittest.mock import patch
        self.app.set_spontaneous_talk(False)
        now = time.monotonic()
        self.app._next_comment = now - 1
        with patch.object(self.app.mind, "spontaneous_event") as spoken:
            self.app._tick()
            spoken.assert_not_called()
        self.app.set_spontaneous_talk(True)
        self.app._next_comment = time.monotonic() - 1
        self.app._last_spoken = -1000
        with (
            patch.object(self.app.computer_voice, "maybe_event", return_value=None),
            patch.object(self.app.mind, "spontaneous_event", wraps=self.app.mind.spontaneous_event) as spoken,
        ):
            self.app._tick()
            spoken.assert_called_once()
        self.assertIsNotNone(self.app._bubble)

    def test_disabling_autonomous_speech_also_suppresses_startup_greeting(self):
        self.app.set_spontaneous_talk(False)
        with patch.object(self.app.mind, "say_event") as spoken:
            self.app._greet_on_start()
            spoken.assert_not_called()

    def test_status_shows_current_emotional_state(self):
        self.app.open_status()
        self.app.state.energy = 8
        self.app.status_panel.refresh()
        self.assertIn("Müde", self.app.status_panel.emotion_label.cget("text"))

    def test_scaling_keeps_feet_on_taskbar(self):
        self.app.toggle_scale()
        self.assertEqual(self.app.settings.scale, 2)
        self.assertEqual(self.app.settings.y, self.app.track.sprite_y(2))
        self.assertEqual(self.app.width, 256)
        self.app.toggle_scale()
        self.assertEqual(self.app.settings.scale, 1)
        self.assertEqual(self.app.settings.y, self.app.track.sprite_y(1))



    def test_restack_groups_sprite_toolbar_and_bubble_without_focusing(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = False
        with patch.object(self.app.root, "focus_force") as focus:
            self.app._on_enter()
            self.app.say("Ich hab dich gesehen.", 9000)
            self.app._move_bubble()
            self.assertEqual(spy.raise_without_focus.call_count, 5)
            # Toolbar show: sprite + toolbar. Bubble show: all three.
            recent = [call.args[0] for call in spy.raise_without_focus.call_args_list[-3:]]
            self.assertEqual(recent, [self.app.root, self.app.toolbar.window, self.app._bubble])
            focus.assert_not_called()

    def test_restack_after_foreign_window_occludes_sprite(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = True
        self.app._on_enter()
        self.app.say("...", 9000)
        spy.raise_without_focus.reset_mock()
        self.app._last_stack_check = time.monotonic() - 100
        with patch.object(self.app.root, "focus_force") as focus:
            self.app._tick()
            self.assertEqual(spy.is_covered.call_count, 1)
            self.assertEqual(
                [call.args[0] for call in spy.raise_without_focus.call_args_list],
                [self.app.root, self.app.toolbar.window, self.app._bubble],
            )
            focus.assert_not_called()

    def test_settings_menu_and_status_follow_sprite_in_layer_order(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        self.app._on_enter()
        self.app.toolbar.settings_button.invoke()
        self.assertIsNotNone(self.app.settings_popup)
        self.assertIs(spy.raise_without_focus.call_args.args[0],
                      self.app.settings_popup.window)
        self.app.settings_popup.close()
        self.app.open_status()
        self.assertIs(spy.raise_without_focus.call_args.args[0],
                      self.app.status_panel.window)

    def test_no_restack_while_windows_are_in_healthy_order(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = False
        self.app._on_enter()
        spy.raise_without_focus.reset_mock()
        self.app._last_stack_check = time.monotonic() - 100
        self.app._tick()
        spy.raise_without_focus.assert_not_called()

    def test_disable_topmost_disables_background_restack(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = True
        self.app.set_topmost(False)
        self.assertFalse(self.app._overlay_stack.enabled)
        self.app._last_stack_check = time.monotonic() - 100
        self.app._tick()
        spy.raise_without_focus.assert_not_called()
        spy.is_covered.assert_not_called()

if __name__ == "__main__":
    unittest.main()
