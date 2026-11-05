"""Validate and serialise the finite RoomClient protocol on its single owner."""

from __future__ import annotations

import json
import sqlite3
import sys
from importlib.metadata import version
from collections import OrderedDict
from typing import Any

from ..application.room_contracts import PROTOCOL_VERSION, ROOM_COMMANDS
from ..application.room_contracts import json_value
from ..application.room_session import RoomSession


class BrowserEndpoint:
    def __init__(self, session: RoomSession) -> None:
        self.session = session
        self._replies: OrderedDict[int, str] = OrderedDict()

    def dispatch_json(self, message: str) -> str:
        request_id = 0
        try:
            if len(message) > 65536:
                raise ValueError("Zimmernachricht ist zu groß.")
            request = json.loads(message)
            if not isinstance(request, dict) or request.get("protocol") != PROTOCOL_VERSION:
                raise ValueError("Unpassendes Zimmerprotokoll.")
            request_id = request.get("requestId")
            if type(request_id) is not int or not 0 < request_id < 2**53:
                raise ValueError("Ungültige Aktionskennung.")
            if request_id in self._replies:
                return self._replies[request_id]
            name, args = request.get("name"), request.get("args", {})
            if name not in ROOM_COMMANDS or not isinstance(args, dict):
                raise ValueError("Unbekannte Zimmeraktion.")
            self.session.execute(name, args)
            reply: dict[str, Any] = {
                "protocol": PROTOCOL_VERSION, "requestId": request_id,
                "ok": True, "snapshot": self.session.snapshot(),
            }
            if name == "forecast":
                reply["forecast"] = json_value(self.session.forecast())
            if name == "snapshot":
                reply["runtime"] = {"python": sys.version.split()[0],
                                    "sqlite": sqlite3.sqlite_version,
                                    "astronomy-engine": version("astronomy-engine"),
                                    "pyjokes": version("pyjokes")}
        except (ValueError, KeyError, TypeError, RuntimeError) as error:
            reply = {"protocol": PROTOCOL_VERSION, "requestId": request_id,
                     "ok": False, "error": str(error)[:300]}
        encoded = json.dumps(reply, ensure_ascii=False, allow_nan=False)
        if request_id:
            self._replies[request_id] = encoded
            while len(self._replies) > 64:
                self._replies.popitem(last=False)
        return encoded
