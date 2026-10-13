"""Pure hardware analytics, safe failures, and real asynchronous monitoring."""

import random
import threading
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from aiko_pet.infrastructure.hardware import os_sensors as activity
from aiko_pet.personality.workload_events import WorkloadEventDetector
from aiko_pet.personality.catalog import DialogueBook
from aiko_pet.infrastructure.hardware.monitor import ActivityMonitor
from aiko_pet.telemetry import ComputerSnapshot, workload_intensity
from aiko_pet.infrastructure.hardware.sampler import HardwareSampler
from aiko_pet.infrastructure.hardware.os_sensors import load_percent
from aiko_pet.infrastructure.hardware.nvidia import parse_nvidia_reading
from aiko_pet.infrastructure.hardware.metrics import percent_label, workload_description


def reading(**kwargs):
    return ComputerSnapshot(measured_at=1000.0, **kwargs)


class HardwareTests(unittest.TestCase):
    def test_cpu_delta_uses_correct_idle_and_kernel_semantics(self):
        self.assertEqual(load_percent((40, 100), (50, 200)), 90.0)
        self.assertEqual(load_percent((20, 100), (120, 200)), 0.0)
        self.assertIsNone(load_percent(None, (30, 200)))
        self.assertIsNone(load_percent((20, 100), (30, 100)))
        self.assertIsNone(load_percent((20, 100), (15, 200)))

    def test_nvidia_reading_fails_closed_and_handles_multiple_gpus(self):
        self.assertEqual(parse_nvidia_reading("76, 6144, 12288\n"), (76.0, 50.0))
        self.assertEqual(parse_nvidia_reading("16, 100, 400\n91, 70, 100"), (91, 70.0))
        self.assertEqual(parse_nvidia_reading("N/A, Not Supported, 0"), (None, None))
        self.assertEqual(parse_nvidia_reading(""), (None, None))
        self.assertEqual(percent_label(None), "–")
        self.assertEqual(percent_label(99.8), "100 %")

    def test_hardware_sampler_has_no_mandatory_gpu_dependency(self):
        # Developer OS may lack NVIDIA tools: no crash and no fake GPU value.
        s = HardwareSampler()
        first = s.sample()
        second = s.sample()
        self.assertIsInstance(first, ComputerSnapshot)
        self.assertIsInstance(second, ComputerSnapshot)
        self.assertIsNotNone(second.measured_at)

    def test_windows_apis_return_real_percentages_and_64bit_uptime(self):
        class FakeTicks:
            restype = None

            def __call__(self):
                return 50 * 3_600_000

        class FakeKernel:
            GetTickCount64 = FakeTicks()

            @staticmethod
            def GetSystemTimes(idle, kernel, user):
                idle._obj.low, kernel._obj.low, user._obj.low = 100, 200, 300
                return 1

            @staticmethod
            def GlobalMemoryStatusEx(status):
                obj = status._obj
                obj.total_phys = 16 * 1024 * 1024 * 1024
                obj.avail_phys = 4 * 1024 * 1024 * 1024
                return 1

        with (
            patch.object(activity.sys, "platform", "win32"),
            patch.object(activity.ctypes, "windll",
                         SimpleNamespace(kernel32=FakeKernel()), create=True),
        ):
            self.assertEqual(activity.cpu_windows_times(), (100, 500))
            self.assertEqual(activity.memory_windows_percent(), 75.0)
            self.assertEqual(activity.uptime_hours(), 50.0)
            self.assertEqual(FakeKernel.GetTickCount64.restype,
                             activity.ctypes.c_uint64)

    def test_monitor_disable_clears_snapshot_and_prevents_sampling(self):
        class StubSampler:
            count = 0

            def sample(self):
                self.count += 1
                return ComputerSnapshot(cpu=85, ram=67, measured_at=100)

        stub = StubSampler()
        monitor = ActivityMonitor(stub, interval_seconds=0.2)
        monitor.set_enabled(False)
        monitor.start()
        time.sleep(0.05)
        self.assertEqual(stub.count, 0)
        monitor.set_enabled(True)
        limit = time.monotonic() + 1.0
        while stub.count == 0 and time.monotonic() < limit:
            time.sleep(0.01)
        self.assertGreater(stub.count, 0)
        self.assertEqual(monitor.latest().cpu, 85)
        monitor.set_enabled(False)
        self.assertIsNone(monitor.latest().cpu)
        monitor.stop()

    def test_monitor_never_blocks_gui_thread_on_slow_sampler(self):
        was_called = threading.Event()
        go = threading.Event()

        class SlowSampler:
            def sample(self):
                was_called.set()
                go.wait(timeout=1)
                return reading(cpu=85)

        monitor = ActivityMonitor(SlowSampler(), interval_seconds=20)
        start = time.monotonic()
        monitor.start()
        self.assertTrue(was_called.wait(timeout=1))
        self.assertLess(time.monotonic() - start, 0.5)
        # Reading the snapshot does not wait on the hardware subprocess.
        self.assertIsNone(monitor.latest().cpu)
        go.set()
        limit = time.monotonic() + 1
        while monitor.latest().cpu is None and time.monotonic() < limit:
            time.sleep(0.01)
        self.assertEqual(monitor.latest().cpu, 85)
        monitor.stop()


class VoiceTests(unittest.TestCase):
    def test_workload_is_perceived_as_effort_not_component_name(self):
        self.assertIsNone(workload_intensity(ComputerSnapshot()))
        self.assertEqual(workload_intensity(reading(cpu=0, gpu=0)), 0.0)
        high_gpu = reading(cpu=10, gpu=96, ram=50)
        gpu_effort = workload_intensity(high_gpu)
        assert gpu_effort is not None
        self.assertGreater(gpu_effort, 0.9)
        self.assertTrue(high_gpu.is_busy())
        # Memory occupancy is not active computation by itself.
        idle_but_occupied = reading(cpu=8, gpu=4, ram=96)
        self.assertFalse(idle_but_occupied.is_busy())
        idle_effort = workload_intensity(idle_but_occupied)
        assert idle_effort is not None
        self.assertLess(idle_effort, 0.3)
        # Pressure still contributes when the computer is already working.
        memory_pressure = workload_intensity(
            reading(cpu=63, gpu=12, ram=96),
        )
        less_pressure = workload_intensity(
            reading(cpu=63, gpu=12, ram=40),
        )
        assert memory_pressure is not None
        assert less_pressure is not None
        self.assertGreater(memory_pressure, less_pressure)
        for snap in (high_gpu, idle_but_occupied):
            self.assertNotIn("GPU", workload_description(snap))
            self.assertNotIn("RAM", workload_description(snap))
            self.assertNotIn("CPU", workload_description(snap))

    def test_classification_is_shared_effort_not_technical_category(self):
        cases = [
            (dict(cpu=94, gpu=93, ram=30), "computer_effort_steady"),
            (dict(cpu=92, gpu=14, ram=30), "computer_effort_steady"),
            (dict(cpu=18, gpu=94, ram=30), "computer_effort_steady"),
            (dict(cpu=5, gpu=10, ram=38), "computer_effort_rest"),
            (dict(cpu=38, gpu=30, ram=38, uptime_hours=14), "computer_uptime"),
            (dict(cpu=35, gpu=22, ram=55), None),
            (dict(), None),
        ]
        for values, expected in cases:
            with self.subTest(values=values):
                self.assertEqual(WorkloadEventDetector.classify(reading(**values)), expected)

    def test_brief_gpu_spike_must_not_claim_exhaustion(self):
        voice = WorkloadEventDetector()
        self.assertIsNone(voice.observe_change(reading(cpu=8, gpu=10), 1000))
        self.assertEqual(voice.observe_change(
            ComputerSnapshot(cpu=12, gpu=96, measured_at=1006), 1006,
        ), "computer_effort_rising")
        event = voice.observe_change(
            ComputerSnapshot(cpu=10, gpu=12, measured_at=1012), 1012,
        )
        self.assertNotIn(event, (
            "computer_effort_recovered_peak", "computer_effort_recovered",
        ))

    def test_sustained_heavy_gpu_load_has_distinct_after_work_reaction(self):
        voice = WorkloadEventDetector()
        self.assertIsNone(voice.observe_change(reading(cpu=7, gpu=5, ram=42), 1000))
        self.assertEqual(voice.observe_change(ComputerSnapshot(
            cpu=9, gpu=95, ram=42, measured_at=1006,
        ), 1006), "computer_effort_rising")
        for stamp in (1012, 1018):
            self.assertIsNone(voice.observe_change(ComputerSnapshot(
                cpu=9, gpu=96, ram=42, measured_at=stamp,
            ), stamp))
        self.assertEqual(voice.observe_change(ComputerSnapshot(
            cpu=9, gpu=97, ram=42, measured_at=1024,
        ), 1024), "computer_effort_peak")
        self.assertEqual(voice.observe_change(ComputerSnapshot(
            cpu=9, gpu=8, ram=43, measured_at=1030,
        ), 1030), "computer_effort_recovered_peak")
        self.assertIsNone(voice.observe_change(ComputerSnapshot(
            cpu=9, gpu=8, ram=43, measured_at=1030,
        ), 1031))
        self.assertIsNone(voice.observe_change(ComputerSnapshot(
            cpu=8, gpu=8, ram=43, measured_at=1036,
        ), 1036))

    def test_gradual_rampdown_still_remembers_recent_heavy_phase(self):
        voice = WorkloadEventDetector()
        voice.observe_change(reading(cpu=5, gpu=5), 1000)
        voice.observe_change(ComputerSnapshot(cpu=80, measured_at=1006), 1006)
        voice.observe_change(ComputerSnapshot(cpu=85, measured_at=1024), 1024)
        voice.observe_change(ComputerSnapshot(cpu=52, measured_at=1030), 1030)
        self.assertEqual(voice.observe_change(ComputerSnapshot(
            cpu=8, measured_at=1036,
        ), 1036), "computer_effort_recovered")

    def test_initial_high_workload_is_not_ignored(self):
        voice = WorkloadEventDetector()
        snap = ComputerSnapshot(cpu=16, gpu=97, ram=52, measured_at=1000)
        self.assertEqual(voice.observe_change(snap, 1000), "computer_effort_rising")
        self.assertIsNone(voice.observe_change(snap, 1001))

    def test_rising_from_cpu_gpu_or_ram_uses_same_voice(self):
        for values in (
            (dict(cpu=6, gpu=6, ram=40), dict(cpu=65, gpu=6, ram=40)),
            (dict(cpu=6, gpu=6, ram=40), dict(cpu=6, gpu=75, ram=40)),
            (dict(cpu=22, gpu=5, ram=30), dict(cpu=38, gpu=5, ram=99)),
        ):
            before, after = values
            with self.subTest(after=after):
                voice = WorkloadEventDetector()
                voice.observe_change(ComputerSnapshot(**before, measured_at=1000), 1000)
                self.assertEqual(voice.observe_change(
                    ComputerSnapshot(**after, measured_at=1006), 1006),
                    "computer_effort_rising")

    def test_stale_duplicate_or_unknown_samples_are_ignored(self):
        voice = WorkloadEventDetector()
        self.assertIsNone(voice.observe_change(ComputerSnapshot(), 1100))
        self.assertIsNone(voice.observe_change(ComputerSnapshot(
            cpu=95, measured_at=1000,
        ), 1100))
        self.assertIsNone(voice.observe_change(ComputerSnapshot(
            cpu=10, measured_at=1100,
        ), 1100))
        self.assertIsNone(voice.observe_change(ComputerSnapshot(
            cpu=10, measured_at=1100,
        ), 1101))
        self.assertIsNone(voice.observe_change(ComputerSnapshot(
            cpu=10, measured_at=1106,
        ), 1106))
        voice.reset_samples()
        self.assertEqual(voice.observe_change(ComputerSnapshot(
            cpu=95, measured_at=1120,
        ), 1120), "computer_effort_rising")

    def test_spontaneous_voice_is_bounded_and_stale_cannot_speak(self):
        voice = WorkloadEventDetector(rng=random.Random(1))
        self.assertIsNone(voice.maybe_event(ComputerSnapshot(cpu=95), 1000))
        self.assertIsNone(voice.maybe_event(reading(cpu=95), 1100))
        self.assertEqual(voice.maybe_event(reading(cpu=95), 1000),
                         "computer_effort_steady")
        self.assertIsNone(voice.maybe_event(reading(cpu=95), 1200))

    def test_every_computer_line_is_characterful_and_never_names_sensors(self):
        from collections import Counter
        book = DialogueBook.from_file()
        counts = Counter(line.event for line in book.lines)
        events = (
            "computer_effort_rising", "computer_effort_heavy",
            "computer_effort_peak", "computer_effort_easing",
            "computer_effort_recovered", "computer_effort_recovered_peak",
            "computer_effort_steady", "computer_effort_rest", "computer_uptime",
        )
        for event in events:
            with self.subTest(event=event):
                self.assertGreaterEqual(counts[event], 5)
        forbidden = ("cpu", "gpu", "ram", "grafikkarte", "prozessor", "vram",
                     "auslastung", "rechenzyklen", "kern", "speicher")
        for line in book.lines:
            if not line.event.startswith("computer_"):
                continue
            self.assertFalse(any(word in line.text.lower() for word in forbidden),
                             line.text)


if __name__ == "__main__":
    unittest.main()
