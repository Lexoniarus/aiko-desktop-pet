"""Functional GUI smoke tests (automatically skipped without a display)."""

import tempfile
import time
import tkinter as tk
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.routine import context_at
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.settings_window import SettingsWindow
from tools.pet_test_support import set_test_pet_values


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
        set_test_pet_values(self.app.state, sleeping=False)

    def _step_walk(self, now: float, elapsed: float) -> str | None:
        return self.app._walk.step(
            now,
            elapsed,
            game_mode=self.app._animated.game_mode,
            attention_active=now < self.app.mind.cursor_attention.attention_until,
        )

    @property
    def toolbar(self) -> ActionToolbar:
        """Require the toolbar created by the test's hover interaction."""
        toolbar = self.app._hover.toolbar
        assert toolbar is not None
        return toolbar

    @property
    def settings_window(self) -> SettingsWindow:
        result = self.app._hover.settings_window
        assert result is not None
        return result

    @property
    def bubble(self) -> tk.Toplevel:
        bubble = self.app._speech.bubble
        assert bubble is not None
        return bubble

    def test_mind_owns_live_cursor_attention(self):
        self.assertIs(
            self.app._cursor_observation.attention,
            self.app.mind.cursor_attention,
        )

    def test_animation_assembly_has_single_state_owners(self):
        self.assertIs(self.app._animation.ambient, self.app._animated._ambient)
        self.assertIs(self.app._animation._walk, self.app._walk)
        self.assertIs(self.app._animation._visual, self.app._visual)

    def test_attention_presentation_has_one_owning_component(self):
        self.assertIs(
            self.app._attention_runtime.attention,
            self.app._attention,
        )

    def test_hover_toolbar_contains_every_care_action(self):
        self.app._hover.show_toolbar()
        self.assertIsNotNone(self.app._hover.toolbar)
        bar = self.toolbar
        self.assertTrue(bar.visible)
        self.assertEqual(
            set(bar.buttons),
            {"place_item", "play", "pet", "sleep", "talk"},
        )
        action_row = bar.buttons["place_item"].master
        labels = [
            child.cget("text")
            for child in action_row.winfo_children()
            if "text" in child.keys()
        ]
        self.assertIn("Unterhalten", labels)
        extra_row = bar.buttons["sleep"].master
        extra_labels = [
            child.cget("text")
            for child in extra_row.winfo_children()
            if "text" in child.keys()
        ]
        self.assertIn("Offen halten", extra_labels)
        bar.buttons["place_item"].invoke()
        menu = self.app._hover.food_menu
        assert menu is not None
        with patch("aiko_pet.application.active_time.ActiveSessionClock.consume",
                   return_value=0):
            menu.buttons["onigiri"].invoke()
        self.assertEqual(self.app.state.satiety, 75)
        self.assertTrue(self.app._world.cursor.carrying)
        bar.refresh()
        self.assertEqual(bar.buttons["sleep"].cget("state"), "disabled")
        self.app._world.cursor.cancel()
        bar.refresh()
        bar.buttons["sleep"].invoke()
        self.assertTrue(self.app.state.sleeping)
        self.assertEqual(bar.buttons["sleep"].cget("text"), "Wecken")
        bar.buttons["sleep"].invoke()
        self.assertFalse(self.app.state.sleeping)

    def test_needs_are_visible_and_updated_in_hover_without_status_popup(self):
        self.app._on_enter()
        bar = self.toolbar
        self.assertFalse(hasattr(self.app._hover, "status_panel"))
        self.assertEqual(
            set(bar.needs),
            {"satiety", "fun", "mood", "energy", "social", "affection", "friendship"},
        )
        for key, _title, _color in bar.NEEDS:
            canvas, rect, label = bar.needs[key]
            self.assertIn("%", label.cget("text"))
            self.assertGreater(canvas.coords(rect)[2], 0)
        set_test_pet_values(self.app.state, mood=22)
        set_test_pet_values(self.app.state, satiety=36)
        set_test_pet_values(self.app.state, energy=95)
        bar.refresh()
        self.assertIn("22%", bar.needs["mood"][2].cget("text"))
        self.assertIn("36%", bar.needs["satiety"][2].cget("text"))
        self.assertIn("95%", bar.needs["energy"][2].cget("text"))
        self.app.root.update()
        self.assertEqual(
            bar.needs["mood"][0].coords(bar.needs["mood"][1])[2],
            round(
                max(
                    bar.needs["mood"][0].winfo_width(),
                    bar.needs["mood"][0].winfo_reqwidth(),
                )
                * 0.22
            ),
        )

    def test_busy_computer_makes_aiko_concentrate_instead_of_walking(self):
        from aiko_pet.telemetry import ComputerSnapshot

        self.app.center()
        original_x = self.app.settings.x
        self.app._walk.movement.remaining_distance = 300
        with patch.object(
            self.app.activity_monitor,
            "latest",
            return_value=ComputerSnapshot(cpu=94, ram=67),
        ):
            self.assertIsNone(self._step_walk(time.monotonic(), 0.2))
            self.assertEqual(self.app._walk.movement.remaining_distance, 0)
            self.assertEqual(original_x, self.app.settings.x)
        self.assertFalse(self.app.state.sleeping)

    def test_disable_hardware_observation_keeps_needs_visible(self):
        self.app._on_enter()
        self.app.set_observe_computer(False)
        self.assertFalse(self.app.settings.observe_computer)
        self.assertIn("deaktiviert", self.toolbar.hardware.cget("text"))
        self.assertIn("Sättigung", self.toolbar.needs["satiety"][2].cget("text"))
        self.app.set_observe_computer(True)
        self.assertTrue(self.app.settings.observe_computer)
        self.assertIn("CPU", self.toolbar.hardware.cget("text"))

    def test_settings_open_update_and_refocus_existing(self):
        self.app._on_enter()
        self.toolbar.settings_button.invoke()
        window = self.settings_window
        self.assertTrue(window.window.winfo_ismapped())
        window.values["auto_walk"].set(False)
        window.checkbuttons["auto_walk"].invoke()
        self.assertTrue(self.app.settings.auto_walk)
        self.toolbar.settings_button.invoke()
        self.assertIs(self.settings_window, window)
        window.close()
        self.assertIsNone(self.app._hover.settings_window)

    def test_outside_click_only_hides_unpinned_toolbar(self):
        self.app._on_enter()
        self.toolbar.settings_button.invoke()
        settings = self.settings_window
        self.app._hover.dismiss_outside(-999, -999)
        self.assertFalse(self.toolbar.visible)
        self.assertIs(self.app._hover.settings_window, settings)
        self.app._hover.show_toolbar()
        self.toolbar.pin_button.invoke()
        self.app._hover.dismiss_outside(-999, -999)
        self.assertTrue(self.toolbar.visible)

    def test_all_100_percent_need_bars_fill_real_display_width(self):
        set_test_pet_values(self.app.state, fun=100)
        set_test_pet_values(self.app.state, satiety=100)
        set_test_pet_values(self.app.state, mood=100)
        set_test_pet_values(self.app.state, energy=100)
        set_test_pet_values(self.app.state, social=100)
        set_test_pet_values(self.app.state, affection=100)
        set_test_pet_values(self.app.state, friendship=100)
        self.app._on_enter()
        self.app.root.update()
        self.toolbar.refresh()
        for key, _title, _color in self.toolbar.NEEDS:
            bar, rect, text = self.toolbar.needs[key]
            self.assertEqual(bar.coords(rect)[2], bar.winfo_width(), key)
            self.assertIn("100%", text.cget("text"))
        set_test_pet_values(self.app.state, mood=25)
        self.toolbar.refresh()
        bar, rect, _text = self.toolbar.needs["mood"]
        self.assertEqual(bar.coords(rect)[2], round(bar.winfo_width() * 0.25))

    def test_side_by_side_bridge_keeps_hover_active(self):
        self.app._on_enter()
        bar = self.toolbar
        bar.window.update_idletasks()
        pet_x, pet_y = self.app.root.winfo_rootx(), self.app.root.winfo_rooty()
        panel_x, panel_y = bar.window.winfo_rootx(), bar.window.winfo_rooty()
        width = bar.window.winfo_width()
        if panel_x >= pet_x + self.app._window.width:
            x = (pet_x + self.app._window.width + panel_x) // 2
        else:
            x = (panel_x + width + pet_x) // 2
        y = max(pet_y, panel_y) + 12
        self.assertTrue(bar.contains_bridge(x, y))
        self.app._hover.last_hover = time.monotonic() - 10
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=x),
            patch.object(self.app.root, "winfo_pointery", return_value=y),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._hover.refresh_hover(time.monotonic())
        self.assertTrue(bar.visible)

    def test_bubble_follows_aiko_and_never_toolbar(self):
        self.app._on_enter()
        assert self.app.settings.x is not None
        assert self.app.settings.y is not None
        self.app._speech.show_text("...Ich schaue zu. Ist das ein Problem?", 6000)
        self.app.root.update_idletasks()
        bubble = self.bubble
        bubble_y = bubble.winfo_rooty()
        self.assertLess(bubble_y + bubble.winfo_height(), self.app.settings.y)
        self.toolbar.window.geometry("+5+5")
        self.toolbar._last_placement = None
        self.app._speech.move()
        self.app.root.update_idletasks()
        self.assertEqual(bubble.winfo_rooty(), bubble_y)
        self.app._place_x(self.app.settings.x - 110)
        self.app.root.update_idletasks()
        self.assertAlmostEqual(
            bubble.winfo_rootx() + bubble.winfo_width() / 2,
            self.app.settings.x + self.app._window.width / 2,
            delta=3,
        )

    def test_drag_toolbar_save_reopen_and_reset_to_aiko(self):
        self.app._on_enter()
        bar = self.toolbar
        original = (bar.window.winfo_rootx(), bar.window.winfo_rooty())
        start = tk.Event()
        start.x_root = original[0] + 20
        start.y_root = original[1] + 20
        bar._drag.start(start)
        self.assertTrue(bar.dragging)
        # Even a click outside while actively dragging must not dismiss it.
        self.app._hover.dismiss_outside(-999, -999)
        self.assertTrue(bar.visible)
        motion = tk.Event()
        motion.x_root = start.x_root + 25
        motion.y_root = start.y_root - 15
        bar._drag.move(motion)
        bar.window.update_idletasks()
        bar._drag.finish(start)
        self.assertFalse(bar.dragging)
        position = (self.app.settings.toolbar_x, self.app.settings.toolbar_y)
        self.assertNotEqual(position, original)
        bar.hide()
        bar.show()
        self.app.root.update_idletasks()
        self.assertEqual(
            (bar.window.winfo_rootx(), bar.window.winfo_rooty()),
            position,
        )
        session_data = self.app.store.load_session(now=time.time())
        _saved, settings = session_data.state, session_data.settings
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
        self.toolbar.place()
        self.app._hover.last_hover = time.monotonic() - 10
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=-999),
            patch.object(self.app.root, "winfo_pointery", return_value=-999),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._hover.refresh_hover(time.monotonic())
        self.assertFalse(self.toolbar.visible)
        self.app._on_enter()
        self.app.root.update()
        self.assertEqual(self.toolbar.window.winfo_rootx(), 25)
        self.assertEqual(self.toolbar.window.winfo_rooty(), 35)

    def test_computer_load_can_trigger_first_person_speech(self):
        from aiko_pet.telemetry import ComputerSnapshot

        self.app._on_enter()
        self.assertIn("CPU", self.toolbar.hardware.cget("text"))
        self.assertIn("GPU", self.toolbar.hardware.cget("text"))
        self.assertIn("RAM", self.toolbar.hardware.cget("text"))
        now = time.monotonic()
        self.app._attention.next_comment = now - 1
        self.app._attention.last_spoken = -9999999
        self.toolbar.hide()
        self.app.settings.spontaneous_talk = True
        self.app._speech.hide()
        self.app._action_playback.until = 0
        with (
            patch.object(
                self.app.activity_monitor,
                "latest",
                return_value=ComputerSnapshot(cpu=92, gpu=15, ram=55, measured_at=now),
            ),
            patch.object(
                self.app.workload_events,
                "maybe_event",
                return_value="computer_effort_steady",
            ),
        ):
            self.app._tick()
            # Work observations can start a review gesture. Speech waits for it.
            self.app._action_playback.until = 0
            self.app._maybe_speak_spontaneously(now + 2)
        self.assertTrue(
            self.app.mind.book.recent[-1].startswith("computer_effort_steady-")
        )

    def test_load_change_updates_visible_voice_and_reaction_with_hover_open(self):
        from aiko_pet.telemetry import ComputerSnapshot

        self.app._on_enter()
        self.app._attention.last_spoken = -1000
        base = time.monotonic()
        first = ComputerSnapshot(cpu=8, gpu=5, ram=40, measured_at=base)
        second = ComputerSnapshot(cpu=89, gpu=5, ram=40, measured_at=base + 7)
        with patch.object(self.app.activity_monitor, "latest", return_value=first):
            self.app._activity.react_to_computer(base, self.app.context)
            self.toolbar.refresh()
            self.assertIn("wenig zu tun", self.toolbar.workload.cget("text"))
        with patch.object(self.app.activity_monitor, "latest", return_value=second):
            self.app._activity.react_to_computer(base + 7, self.app.context)
            self.toolbar.refresh()
            self.assertIn("deutlich erhöht", self.toolbar.workload.cget("text"))
            self.assertIsNotNone(self.app._activity.pending_computer_line)
            self.app._activity.react_to_computer(base + 10, self.app.context)
        self.assertTrue(self.toolbar.visible)
        self.assertIsNone(self.app._activity.pending_computer_line)
        self.assertTrue(
            next(
                line
                for line in self.app.mind.book.lines
                if line.id == self.app.mind.book.recent[-1]
            ).event
            == "computer_effort_rising"
        )
        self.assertIsNotNone(self.app._speech.bubble)

    def test_character_cannot_be_dragged_and_is_always_grounded(self):
        self.assertFalse(self.app.canvas.bind("<B1-Motion>"))
        self.assertEqual(
            self.app.settings.y,
            self.app._window.track.sprite_y(self.app.settings.scale),
        )
        y = self.app.settings.y
        self.app._place_x(-400)
        self.assertEqual(self.app.settings.x, self.app._window.track.left)
        self.app._place_x(99999)
        self.assertEqual(
            self.app.settings.x, self.app._window.track.right - self.app._window.width
        )
        self.assertEqual(self.app.settings.y, y)

    def test_walk_is_horizontal_and_stops_on_hover(self):
        self.app.center()
        original_y = self.app.settings.y
        original_x = self.app.settings.x
        assert original_x is not None
        self._step_walk(time.monotonic(), 0)
        self.app._walk.movement.remaining_distance = 140
        state = self._step_walk(time.monotonic(), 0.15)
        self.assertEqual(state, "running-right")
        assert self.app.settings.x is not None
        self.assertGreater(self.app.settings.x, original_x)
        self.assertEqual(self.app.settings.y, original_y)
        self.app._on_enter()
        self.assertIsNone(self._step_walk(time.monotonic(), 0.15))
        self.assertEqual(self.app._walk.movement.remaining_distance, 0)

    def test_toolbar_auto_hides_only_when_pointer_has_left(self):
        self.app._on_enter()
        self.app._hover.last_hover = time.monotonic() - 10
        with (
            patch.object(self.app.root, "winfo_pointerx", return_value=-999),
            patch.object(self.app.root, "winfo_pointery", return_value=-999),
            patch.object(self.app.root, "winfo_containing", return_value=None),
        ):
            self.app._hover.refresh_hover(time.monotonic())
        self.assertFalse(self.toolbar.visible)

    def test_far_away_desktop_cursor_still_gets_a_gaze_frame(self):
        self.assertEqual(self.app._visual.gaze_direction((99999, -99999)), 2)
        self.assertIn(self.app._visual.gaze_direction((-99999, -99999)), (14, 15))
        self.app.set_follow_cursor(False)
        self.assertIsNone(self.app._visual.gaze_direction((99999, -99999)))

    def test_hover_bar_has_clock_and_meal_aware_button(self):
        from datetime import datetime

        from aiko_pet.pet.routine import context_at

        morning = datetime(2026, 10, 12, 8, 20).astimezone().timestamp()
        self.app.context = context_at(morning)
        set_test_pet_values(self.app.state, meals_date="")
        self.app._on_enter()
        self.assertIn("Montag", self.toolbar.today.cget("text"))
        self.assertEqual(self.toolbar.buttons["place_item"].cget("text"), "Frühstück")
        self.app.state.interact("feed", now=morning)
        self.toolbar.refresh()
        self.assertEqual(self.toolbar.buttons["place_item"].cget("text"), "Snack")

    def test_startup_geometry_is_explicitly_applied_before_first_frame(self):
        # Covers the original flash at (0,0) and saved coordinates which
        # already happen to match the taskbar's calculated start position.
        self.assertTrue(self.app._window.placed)
        self.assertEqual(self.app.root.state(), "normal")
        self.assertEqual(self.app.root.winfo_x(), self.app.settings.x)
        self.assertEqual(self.app.root.winfo_y(), self.app.settings.y)
        self.app._window.placed = False
        self.app.root.geometry("192x208+0+0")
        position = self.app.settings.x
        assert position is not None
        self.app._place_x(position)
        self.app.root.update_idletasks()
        self.assertEqual(self.app.root.winfo_x(), self.app.settings.x)
        self.assertEqual(self.app.root.winfo_y(), self.app.settings.y)

    def test_left_and_right_click_open_voice_reactions(self):
        self.app._runtime.stop()
        # Dialogue expectations are daytime-specific, never test local time.
        self.app.context = context_at(
            datetime(2026, 10, 12, 15, 0).timestamp(),
        )
        self.assertIn("_on_click_left", str(self.app.canvas.bind("<Button-1>")))
        self.assertIn("_on_click_right", str(self.app.canvas.bind("<Button-3>")))
        self.app._on_click_left()
        self.assertIsNotNone(self.app._speech.bubble)
        self.assertEqual(
            next(
                line.event
                for line in self.app.mind.book.lines
                if line.id == self.app.mind.book.recent[-1]
            ),
            "click_left",
        )
        deadline = time.monotonic() + 6
        while not self.app._contact.can_interact("pet") and time.monotonic() < deadline:
            self.app.root.update()
            time.sleep(.02)
        self.assertTrue(self.app._contact.can_interact("pet"))
        self.app._on_click_right()
        self.assertIsNotNone(self.app._speech.bubble)
        self.assertEqual(
            next(
                line.event
                for line in self.app.mind.book.lines
                if line.id == self.app.mind.book.recent[-1]
            ),
            "click_right",
        )
        self.assertTrue(self.toolbar.visible)

    def test_speech_bubble_includes_a_pixel_tail(self):
        self.app._speech.show_text("...Ich habe dich bemerkt.", 6000)
        bubble = self.bubble
        self.assertIsNotNone(bubble)
        self.assertEqual(len(bubble.winfo_children()), 2)
        tail = bubble.winfo_children()[-1]
        self.assertIsInstance(tail, tk.Canvas)
        assert isinstance(tail, tk.Canvas)
        self.assertEqual(len(tail.find_all()), 1)
        self.app._speech.hide()
        self.assertIsNone(self.app._speech.bubble)

    def test_chatter_switch_suppresses_autonomous_lines(self):
        from unittest.mock import patch

        self.app.set_spontaneous_talk(False)
        now = time.monotonic()
        self.app._attention.next_comment = now - 1
        with patch.object(self.app.mind, "select_spontaneous_reaction") as spoken:
            self.app._tick()
            spoken.assert_not_called()
        self.app.set_spontaneous_talk(True)
        self.app._attention.next_comment = time.monotonic() - 1
        self.app._attention.last_spoken = -1000
        with (
            patch.object(self.app.workload_events, "maybe_event", return_value=None),
            patch.object(
                self.app.mind,
                "select_spontaneous_reaction",
                wraps=self.app.mind.select_spontaneous_reaction,
            ) as spoken,
        ):
            self.app._tick()
            spoken.assert_called_once()
        self.assertIsNotNone(self.app._speech.bubble)

    def test_disabling_autonomous_speech_also_suppresses_startup_greeting(self):
        self.app.set_spontaneous_talk(False)
        with patch.object(self.app.mind, "select_reaction") as spoken:
            self.app._greet_on_start()
            spoken.assert_not_called()

    def test_status_details_show_emotion_in_toolbar(self):
        self.app._hover.open_status()
        self.toolbar.toggle_details()
        set_test_pet_values(self.app.state, energy=8)
        self.toolbar.refresh()
        assert self.toolbar.details is not None
        self.assertIn("Müde", self.toolbar.details.text("emotion"))

    def test_scaling_keeps_feet_on_taskbar(self):
        self.app.toggle_scale()
        self.assertEqual(self.app.settings.scale, 2)
        self.assertEqual(self.app.settings.y, self.app._window.track.sprite_y(2))
        self.assertEqual(self.app._window.width, 384)
        self.app.toggle_scale()
        self.assertEqual(self.app.settings.scale, 1)
        self.assertEqual(self.app.settings.y, self.app._window.track.sprite_y(1))

    def test_restack_groups_sprite_toolbar_and_bubble_without_focusing(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = False
        with patch.object(self.app.root, "focus_force") as focus:
            self.app._on_enter()
            self.app._speech.show_text("Ich hab dich gesehen.", 9000)
            self.app._speech.move()
            self.assertEqual(spy.raise_without_focus.call_count, 5)
            # Toolbar show: sprite + toolbar. Bubble show: all three.
            recent = [
                call.args[0] for call in spy.raise_without_focus.call_args_list[-3:]
            ]
            self.assertEqual(
                recent, [self.app.root, self.toolbar.window, self.app._speech.bubble]
            )
            focus.assert_not_called()

    def test_restack_after_foreign_window_occludes_sprite(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = True
        self.app._on_enter()
        self.app._speech.show_text("...", 9000)
        spy.raise_without_focus.reset_mock()
        self.app._maintenance.last_stack_check = time.monotonic() - 100
        with patch.object(self.app.root, "focus_force") as focus:
            self.app._tick()
            self.assertEqual(spy.is_covered.call_count, 1)
            self.assertEqual(
                [call.args[0] for call in spy.raise_without_focus.call_args_list],
                [self.app.root, self.toolbar.window, self.app._speech.bubble],
            )
            focus.assert_not_called()

    def test_settings_and_toolbar_stay_in_window_stack(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        self.app._on_enter()
        self.toolbar.settings_button.invoke()
        self.assertIs(
            spy.raise_without_focus.call_args.args[0], self.settings_window.window
        )
        self.settings_window.close()
        self.app._hover.open_status()
        self.assertIs(spy.raise_without_focus.call_args.args[0], self.toolbar.window)

    def test_no_restack_while_windows_are_in_healthy_order(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = False
        self.app._on_enter()
        spy.raise_without_focus.reset_mock()
        self.app._maintenance.last_stack_check = time.monotonic() - 100
        self.app._tick()
        spy.raise_without_focus.assert_not_called()

    def test_disable_topmost_disables_background_restack(self):
        self.app._overlay_stack._backend = spy = Mock()
        spy.raise_without_focus.return_value = True
        spy.is_covered.return_value = True
        self.app.set_topmost(False)
        self.assertFalse(self.app._overlay_stack.enabled)
        self.app._maintenance.last_stack_check = time.monotonic() - 100
        self.app._tick()
        spy.raise_without_focus.assert_not_called()
        spy.is_covered.assert_not_called()


if __name__ == "__main__":
    unittest.main()
