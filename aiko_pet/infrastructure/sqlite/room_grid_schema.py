"""Add a geometry version, preserving original v6 rows until explicit recovery."""

from .world_schema import WORLD_SCHEMA

ROOM_GRID_SCHEMA = (
    "ALTER TABLE room_state RENAME TO legacy_room_state",
    """CREATE TABLE room_state (
        id INTEGER PRIMARY KEY REFERENCES world_state(id) ON DELETE CASCADE CHECK(id=1),
        environment TEXT NOT NULL CHECK(environment='aiko_room'),
        pet_x REAL NOT NULL CHECK(pet_x >= 0),
        pet_depth REAL NOT NULL CHECK(pet_depth >= 0),
        object_depths TEXT NOT NULL,
        geometry_version INTEGER NOT NULL CHECK(geometry_version IN (1,2)),
        layout_id TEXT NOT NULL,
        layout_revision INTEGER NOT NULL CHECK(layout_revision > 0)
    )""",
    "INSERT INTO room_state SELECT *,1,'aiko-home',1 FROM legacy_room_state",
    "DROP TABLE legacy_room_state",
    "CREATE TEMP TABLE saved_room_memory_sources AS "
    "SELECT * FROM object_memory_sources",
    "DROP TABLE object_memory_sources",
    "ALTER TABLE object_memories RENAME TO legacy_room_object_memories",
    WORLD_SCHEMA[3]
    .replace("('food', 'drink')", "('food', 'drink', 'book')")
    .replace(
        "CHECK((identity IS NULL)",
        "depth REAL NOT NULL DEFAULT 0.9 CHECK(depth >= 0), CHECK((identity IS NULL)",
    ),
    "INSERT INTO object_memories SELECT * FROM legacy_room_object_memories",
    "DROP TABLE legacy_room_object_memories",
    WORLD_SCHEMA[4],
    "INSERT INTO object_memory_sources SELECT * FROM saved_room_memory_sources",
    "DROP TABLE saved_room_memory_sources",
)
