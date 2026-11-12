"""Exercise the local HTTP and browser lifecycle independently of Tk."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.desktop import version_launcher


class LocalRoomServerTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = self.enterContext(tempfile.TemporaryDirectory())
        starter = Path(folder)
        for filename in ("index.html", "sw.js"):
            (starter / filename).touch()
        self.room = version_launcher.LocalRoomServer(starter)
        self.addCleanup(self.room.close)
        self.server = self.enterContext(
            patch.object(version_launcher, "RoomHTTPServer")
        )
        self.thread = self.enterContext(patch.object(version_launcher, "Thread"))
        self.browser = self.enterContext(
            patch.object(version_launcher.webbrowser, "open_new_tab")
        )

    def test_marked_browser_start_and_idempotent_shutdown(self) -> None:
        self.room.open()
        self.room.close()
        self.room.close()

        self.assertEqual(self.server.call_args.args[0], ("127.0.0.1", 8940))
        self.browser.assert_called_once_with("http://127.0.0.1:8940/?local-launch=1")
        self.server.return_value.shutdown.assert_called_once_with()
        self.server.return_value.server_close.assert_called_once_with()

    def test_busy_port_never_opens_browser(self) -> None:
        self.server.side_effect = OSError("Address already in use")
        with self.assertRaisesRegex(OSError, "Address already in use"):
            self.room.open()

        self.room.close()
        self.thread.assert_not_called()
        self.browser.assert_not_called()

    def test_browser_refusal_releases_the_listener(self) -> None:
        self.browser.return_value = False
        with self.assertRaisesRegex(RuntimeError, "Standardbrowser"):
            self.room.open()

        self.room.close()
        self.server.return_value.shutdown.assert_called_once_with()
        self.server.return_value.server_close.assert_called_once_with()
