"""DPI virtualization is corrected only for Windows' unaware coordinate space."""

import unittest
from unittest.mock import Mock, patch

from aiko_pet.ui.common.display_metrics import virtualization_factor


class DisplayMetricsTests(unittest.TestCase):
    def test_only_unaware_process_uses_the_primary_monitor_scale(self):
        for awareness in (0, 1, 2):
            with self.subTest(awareness=awareness):
                shcore, user32 = Mock(), Mock()

                def read_awareness(_process, result):
                    result._obj.value = awareness
                    return 0

                def read_scale(_monitor, result):
                    result._obj.value = 150
                    return 0

                shcore.GetProcessDpiAwareness.side_effect = read_awareness
                shcore.GetScaleFactorForMonitor.side_effect = read_scale
                user32.MonitorFromPoint.return_value = 123
                with (
                    patch('aiko_pet.ui.common.display_metrics.sys.platform', 'win32'),
                    patch('ctypes.WinDLL', create=True, side_effect=lambda name, **_kw:
                          shcore if name == 'shcore' else user32),
                ):
                    self.assertEqual(virtualization_factor(),
                                     1.5 if awareness == 0 else 1)
                self.assertEqual(shcore.GetScaleFactorForMonitor.call_count,
                                 1 if awareness == 0 else 0)

    def test_unavailable_windows_api_leaves_reported_coordinates_unchanged(self):
        with (
            patch('aiko_pet.ui.common.display_metrics.sys.platform', 'win32'),
            patch('ctypes.WinDLL', create=True, side_effect=OSError),
        ):
            self.assertEqual(virtualization_factor(), 1)

    def test_other_platforms_do_not_load_windows_libraries(self):
        with (
            patch('aiko_pet.ui.common.display_metrics.sys.platform', 'linux'),
            patch('ctypes.WinDLL', create=True) as native,
        ):
            self.assertEqual(virtualization_factor(), 1)
            native.assert_not_called()
