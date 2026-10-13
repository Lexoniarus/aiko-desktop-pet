"""Sensor modules preserve the old API and keep GPU subprocesses optional."""

from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

import aiko_pet.system_activity as activity
from aiko_pet.infrastructure.hardware.monitor import ActivityMonitor
from aiko_pet.infrastructure.hardware.sampler import HardwareSampler
from aiko_pet.infrastructure.hardware.metrics import (
    ComputerSnapshot, workload_intensity,
)
from aiko_pet.infrastructure.hardware.nvidia import parse_nvidia_reading
from aiko_pet.infrastructure.hardware.os_sensors import load_percent


class SensorBoundaryTests(unittest.TestCase):
    def test_legacy_imports_are_exactly_the_new_public_types(self) -> None:
        self.assertIs(activity.HardwareSampler, HardwareSampler)
        self.assertIs(activity.ActivityMonitor, ActivityMonitor)
        self.assertIs(activity.ComputerSnapshot, ComputerSnapshot)
        self.assertIs(activity.workload_intensity, workload_intensity)
        self.assertIs(activity.parse_nvidia_reading, parse_nvidia_reading)
        self.assertIs(activity.load_percent, load_percent)

    def test_injected_os_and_nvidia_values_preserve_smoothing(self) -> None:
        result = subprocess.CompletedProcess(
            args=["fake-nvidia"], returncode=0,
            stdout="90, 6144, 12288\n20, 100, 400\n", stderr="",
        )
        with (
            patch("aiko_pet.infrastructure.hardware.sampler.nvidia_executable",
                  return_value="fake-nvidia"),
            patch("aiko_pet.infrastructure.hardware.sampler.sys.platform", "linux"),
            patch("aiko_pet.infrastructure.hardware.sampler.cpu_linux_times",
                  side_effect=[(50, 100), (70, 200)]),
            patch("aiko_pet.infrastructure.hardware.sampler.memory_linux_percent",
                  return_value=38.5),
            patch("aiko_pet.infrastructure.hardware.sampler.uptime_hours",
                  return_value=8.25),
            patch("aiko_pet.infrastructure.hardware.sampler.subprocess.run",
                  return_value=result) as runner,
        ):
            sampler = HardwareSampler()
            first = sampler.sample()
            second = sampler.sample()
        self.assertIsNone(first.cpu)
        self.assertEqual(second.cpu, 80.0)
        self.assertEqual(second.gpu, 90.0)
        self.assertEqual(second.gpu_memory, 50.0)
        self.assertEqual(second.ram, 38.5)
        self.assertEqual(second.uptime_hours, 8.25)
        self.assertEqual(runner.call_count, 2)
        self.assertEqual(runner.call_args.kwargs["timeout"], 2.0)

    def test_absent_gpu_and_unsupported_system_never_fabricate_zero(self) -> None:
        with (
            patch("aiko_pet.infrastructure.hardware.sampler.nvidia_executable",
                  return_value=None),
            patch("aiko_pet.infrastructure.hardware.sampler.sys.platform", "other"),
        ):
            result = HardwareSampler().sample()
        self.assertIsNone(result.cpu)
        self.assertIsNone(result.gpu)
        self.assertIsNone(result.gpu_memory)
        self.assertIsNone(result.ram)


if __name__ == "__main__":
    unittest.main()
