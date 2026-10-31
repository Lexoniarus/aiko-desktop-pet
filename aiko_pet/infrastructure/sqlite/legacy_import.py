"""One-time strict legacy import, without offline simulation."""

from __future__ import annotations

import time

from ...application.session import LoadedPetData
from ...pet.food_catalog import DEFAULT_CATALOG
from ...world.contracts import ObjectDefinition
from ..item_assets import load_item_catalog
from ..legacy_json_codec import decode_legacy_session
from ..save_paths import SavePaths
from ..world_catalog import build_consumable_definitions
from .backups import backup_legacy_json
from .errors import storage_failures
from .rows import nonnegative
from .store import SqliteStateStore


def load_or_import_session(
    paths: SavePaths, *, now: float | None = None,
    definitions: tuple[ObjectDefinition, ...] | None = None,
) -> LoadedPetData:
    """Use only the selected database/source, stopping on any present bad save.

    Absence is handled explicitly; errors never select a different source or
    reset an existing file. A completed SQLite checkpoint is always authoritative.
    """
    store = SqliteStateStore(paths.database, definitions=definitions)
    with storage_failures(paths.database):
        try:
            paths.database.stat()
        except FileNotFoundError:
            pass
        else:
            return store.load_session(now=now)
    with storage_failures(paths.legacy_json):
        try:
            contents = paths.legacy_json.read_bytes()
        except FileNotFoundError:
            contents = None
    if contents is None:
        return store.load_session(now=now)
    with storage_failures(paths.legacy_json):
        current = nonnegative(time.time() if now is None else now, "import UTC time")
        catalog = (definitions if definitions is not None else
                   build_consumable_definitions(DEFAULT_CATALOG, load_item_catalog()))
        loaded = decode_legacy_session(contents, catalog, now=current)
        backup_legacy_json(paths.legacy_json, contents)
    store.initialize_legacy_session(loaded, imported_at=current)
    return store.load_session(now=now)
