"""Construct one local Python room without importing Tk or hardware observers."""

from __future__ import annotations

import time
from pathlib import Path

from ..application.room_session import RoomSession
from ..infrastructure.browser.persistence import publish_browser_database
from ..infrastructure.character_assets import load_character_catalog
from ..infrastructure.character_mind import make_aiko_mind
from ..infrastructure.item_assets import load_item_catalog
from ..infrastructure.sqlite.store import SqliteStateStore
from ..infrastructure.world_catalog import build_world_definitions
from ..pet.food_catalog import DEFAULT_CATALOG
from ..world.contracts import WorldSurface
from ..world.state import WorldState
from .endpoint import BrowserEndpoint


def create_browser_session(path: str) -> BrowserEndpoint:
    definitions = build_world_definitions(DEFAULT_CATALOG, load_item_catalog())
    store = SqliteStateStore(Path(path), definitions=definitions,
                             publish=publish_browser_database)
    loaded = store.load_session()
    session = RoomSession(
        store, loaded, make_aiko_mind(started_at=time.monotonic()),
        WorldState(WorldSurface(5100, 900, 24), definitions), load_character_catalog(),
    )
    session.save()
    return BrowserEndpoint(session)
