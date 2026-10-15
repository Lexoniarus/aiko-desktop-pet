"""Import and hardware event contracts after WorkloadEventDetector extraction."""

import unittest

from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.telemetry import ComputerSnapshot


class WorkloadEventTests(unittest.TestCase):
    def test_missing_telemetry_produces_no_workload_event(self) -> None:
        workload_events = WorkloadEventDetector()
        missing = ComputerSnapshot(measured_at=0)
        self.assertIsNone(workload_events.observe_change(missing, now=1.0))
        self.assertIsNone(workload_events.maybe_event(missing, now=1.0))
        self.assertIsNone(workload_events.classify(missing))


if __name__ == "__main__":
    unittest.main()
