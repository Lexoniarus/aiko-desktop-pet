"""Run repository tests locally with native Tk disabled and measured durations.

Native widget fixtures use their existing display-unavailable skips. This is
not native Windows visual/input acceptance. Default saves are redirected into a
temporary directory; individual tests retain their own isolated fixtures.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from typing import Any, NoReturn
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class NativeTkDisabled(tk.TclError):
    """A native-only case cannot execute under the explicit no-window contract."""


def reject_native_tk(*_args: Any, **_kwargs: Any) -> NoReturn:
    raise NativeTkDisabled("Native Tk disabled for this local no-window run")


class TimedResult(unittest.TextTestResult):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.timings: dict[str, float] = {}
        self._started = 0.0

    def addError(self, test: unittest.TestCase, err: Any) -> None:  # noqa: N802
        if isinstance(err[1], NativeTkDisabled):
            self.addSkip(test, str(err[1]))
        else:
            super().addError(test, err)

    def startTest(self, test: unittest.TestCase) -> None:  # noqa: N802 - unittest protocol
        self._started = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test: unittest.TestCase) -> None:  # noqa: N802 - unittest protocol
        seconds = time.perf_counter() - self._started
        self.timings[test.id()] = seconds
        if seconds > 10:
            self.stream.writeln(f"\nOver 10 seconds: {test.id()} ({seconds:.3f}s)")
            self.stream.flush()
        super().stopTest(test)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    with (
        tempfile.TemporaryDirectory(prefix="aiko-local-suite-") as folder,
        patch.dict(os.environ, {"AIKO_SAVE_PATH": str(Path(folder) / "state.json")}),
        patch("_tkinter.create", side_effect=reject_native_tk),
    ):
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
        result = unittest.TextTestRunner(verbosity=1, resultclass=TimedResult).run(
            suite
        )
    assert isinstance(result, TimedResult)
    slowest = sorted(result.timings.items(), key=lambda row: row[1], reverse=True)
    for name, seconds in slowest[:12]:
        print(f"{seconds:.3f}s {name}", flush=True)
    if args.report is not None:
        args.report.write_text(
            json.dumps(
                {
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors),
                    "skipped": [(str(test), reason) for test, reason in result.skipped],
                    "timings": dict(slowest),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
