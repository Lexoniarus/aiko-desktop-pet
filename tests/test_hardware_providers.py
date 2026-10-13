"""Injected sensor providers keep GPU subprocesses optional."""

from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from aiko_pet.infrastructure.hardware.sampler import HardwareSampler


class SensorBoundaryTests(unittest.TestCase):
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
