"""Choose a source-checkout version and own the local room server."""

from __future__ import annotations

import os
import webbrowser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from tkinter import Tk, messagebox, ttk
from typing import BinaryIO

ROOM_HOST = "127.0.0.1"
ROOM_PORT = 8940
ROOM_ADDRESS = f"{ROOM_HOST}:{ROOM_PORT}"
LOCAL_LAUNCH_PATH = "/?local-launch=1"
ROOM_URL = f"http://{ROOM_ADDRESS}{LOCAL_LAUNCH_PATH}"


class RoomHTTPServer(ThreadingHTTPServer):
    # On Windows, SO_REUSEADDR can allow a second live listener on the port.
    allow_reuse_address = os.name != "nt"


class RoomRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self) -> BinaryIO | None:
        if self.headers.get("Host") != ROOM_ADDRESS:
            self.send_error(HTTPStatus.FORBIDDEN)
            return None
        return super().send_head()

    def end_headers(self) -> None:
        if self.path in (LOCAL_LAUNCH_PATH, "/install.json"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def list_directory(self, path: str | os.PathLike[str]) -> None:
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        # The launcher also works under pythonw, which has no console.
        pass


def choose_desktop(starter: Path) -> bool:
    """Return true only if the user selected the existing desktop entry point."""
    root = Tk()
    root.title("Aiko starten")
    root.resizable(False, False)
    body = ttk.Frame(root, padding=20)
    body.pack(fill="both", expand=True)
    title = ttk.Label(body, text="Welche Version möchtest du starten?")
    title.pack(pady=(0, 14))

    desktop_selected = False
    room_server: RoomHTTPServer | None = None

    def select_desktop() -> None:
        nonlocal desktop_selected
        desktop_selected = True
        root.destroy()

    def stop_room() -> None:
        nonlocal room_server
        if room_server is not None:
            room_server.shutdown()
            room_server.server_close()
            room_server = None

    def close() -> None:
        stop_room()
        root.destroy()

    def select_room() -> None:
        nonlocal room_server
        required = ("index.html", "sw.js")
        if not all((starter / name).is_file() for name in required):
            messagebox.showerror(
                "Raum-Version",
                f"Der lokale Raum-Build fehlt.\n\n{starter}",
                parent=root,
            )
            return
        handler = partial(RoomRequestHandler, directory=str(starter))
        try:
            server = RoomHTTPServer((ROOM_HOST, ROOM_PORT), handler)
            thread = Thread(
                target=server.serve_forever,
                kwargs={"poll_interval": 0.1},
                name="Aiko Room HTTP",
                daemon=True,
            )
            try:
                thread.start()
            except RuntimeError:
                server.server_close()
                raise
            room_server = server
            if not webbrowser.open_new_tab(ROOM_URL):
                raise RuntimeError("Der Standardbrowser konnte nicht geöffnet werden.")
        except (OSError, RuntimeError, webbrowser.Error) as error:
            stop_room()
            messagebox.showerror(
                "Raum-Version",
                f"Aikos Zimmer konnte nicht gestartet werden.\n\n{error}",
                parent=root,
            )
            return

        root.title("Aikos Zimmer")
        title.config(text="Die Raum-Version läuft im Browser.")
        desktop_button.pack_forget()
        room_button.pack_forget()
        ttk.Label(body, text="Schließe zuerst den Raum-Tab im Browser.").pack(
            pady=(0, 8),
        )
        ttk.Button(body, text="Raum beenden", command=close).pack(fill="x")

    desktop_button = ttk.Button(body, text="Desktop-Version", command=select_desktop)
    desktop_button.pack(fill="x", pady=(0, 6))
    room_button = ttk.Button(body, text="Raum-Version", command=select_room)
    room_button.pack(fill="x")
    desktop_button.focus_set()
    root.protocol("WM_DELETE_WINDOW", close)
    try:
        root.mainloop()
    finally:
        stop_room()
    return desktop_selected
